#!/usr/bin/env python3
"""
Servidor API REST para el sistema RAG.

Ejecuta el servidor FastAPI con el servicio RAG inicializado.

Uso:
    python run_api.py

    O con configuración personalizada:
    HOST=0.0.0.0 PORT=8000 python run_api.py

Endpoints disponibles:
    GET  /api/v1/health          - Health check
    GET  /api/v1/metrics         - Métricas del sistema
    POST /api/v1/query           - Consulta RAG
    POST /api/v1/query/stream    - Consulta RAG con streaming
    POST /api/v1/ingest/file     - Ingerir archivo
    POST /api/v1/ingest/directory - Ingerir directorio
    GET  /api/v1/documents       - Listar documentos
    DELETE /api/v1/documents     - Eliminar documento

Documentación interactiva:
    http://localhost:8000/docs   - Swagger UI
    http://localhost:8000/redoc  - ReDoc
"""

import os
import sys
import argparse
import logging

from dotenv import load_dotenv
from rich.console import Console

# Cargar variables de entorno
load_dotenv()

# Inicializar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

console = Console()


def initialize_rag_service():
    """Inicializa el servicio RAG para la API."""
    from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
    from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
    from src.infrastructure.adapters.llama_cpp_llm_adapter import LlamaCppLLMAdapter
    from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter
    from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter
    from src.application.services.rag_service import RAGService

    console.print("[bold cyan]=== INICIALIZANDO SERVIDOR API RAG ===[/]")

    # Validar dependencias
    missing = []
    for mod in ("langchain", "chromadb", "llama_cpp"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        console.print(f"[red][!] Error: Faltan dependencias: {', '.join(missing)}[/]")
        sys.exit(1)

    # Configuración
    embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    default_model = "./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    model_path = os.getenv("LLAMA_CPP_MODEL_PATH", default_model)
    chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    top_k = int(os.getenv("TOP_K_DOCUMENTS", "4"))
    n_gpu_layers = int(os.getenv("N_GPU_LAYERS", "0"))
    n_ctx = int(os.getenv("N_CTX", "4096"))

    # Validar modelo
    if not os.path.exists(model_path):
        # Bootstrap automático: descarga TinyLlama si no hay modelo configurado
        if model_path == default_model:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            model_url = (
                "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/"
                "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
            )
            console.print("[yellow][!] Modelo no encontrado, descargando TinyLlama-1.1B (~780 MB)...[/]")
            import urllib.request
            urllib.request.urlretrieve(model_url, model_path)
            console.print("[green]    ✓ Modelo descargado.[/]")
        else:
            console.print(f"[red][!] ERROR: Modelo GGUF no encontrado en: {model_path}[/]")
            console.print(f"[yellow]    Descarga un modelo o vuelve al default: {default_model}[/]")
            sys.exit(1)

    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    if size_mb < 100:
        console.print(f"[red][!] ERROR: Modelo incompleto ({size_mb:.1f} MB < 100 MB)[/]")
        sys.exit(1)
    with open(model_path, "rb") as f:
        header = f.read(4)
    if header != b"GGUF":
        console.print("[red][!] ERROR: Modelo corrupto (header inválido)[/]")
        sys.exit(1)

    console.print("[yellow][*] Cargando componentes...[/]")

    # Cargar embeddings
    console.print(f"[yellow]    → Embeddings: {embedding_model}[/]")
    embedding_adapter = HFEmbeddingAdapter(model_name=embedding_model)
    console.print("[green]    ✓ Embeddings listo.[/]")

    # Cargar LLM
    model_name = os.path.basename(model_path)
    gpu_info = f"(GPU: {n_gpu_layers} capas)" if n_gpu_layers > 0 else "(CPU)"
    console.print(f"[yellow]    → LLM: {model_name} {gpu_info}[/]")
    llm_adapter = LlamaCppLLMAdapter(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )
    console.print("[green]    ✓ LLM listo.[/]")

    # Cargar loader
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
    loader_adapter = LangChainLoaderAdapter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Cargar ChromaDB
    console.print(f"[yellow]    → ChromaDB: {chroma_db_path}[/]")
    doc_store_adapter = ChromaDBAdapter(
        embedding_port=embedding_adapter,
        persist_directory=chroma_db_path
    )
    console.print("[green]    ✓ ChromaDB listo.[/]")

    # Crear LangChain RAG Adapter (desacoplado)
    prompt_template = """
Eres un Ingeniero de IA especializado en sistemas RAG locales. Tu misión es responder preguntas
utilizando ÚNICAMENTE el contexto proporcionado a continuación de forma técnica, clara y precisa.

CONTEXTO PROPORCIONADO:
{context}

REGLAS:
1. Responde basándote exclusivamente en el contexto.
2. Si la respuesta no está en el contexto, indica amablemente que no tienes esa información localmente.
3. Mantén un tono profesional y técnico en español.
4. No inventes hechos ni detalles técnicos que no aparezcan en el contexto.

PREGUNTA DEL USUARIO: {input}

RESPUESTA TÉCNICA:
"""

    rag_chain = LangChainRAGAdapter(
        llm_adapter=llm_adapter,
        doc_store=doc_store_adapter,
        prompt_template=prompt_template,
        top_k=top_k
    )

    # Crear RAGService con chain desacoplado
    rag_service = RAGService(
        chain=rag_chain,
        doc_store_adapter=doc_store_adapter,
        loader_adapter=loader_adapter,
        top_k=top_k
    )

    console.print("[green][+] SISTEMA RAG OPERATIVO[/]")
    console.print(f"[cyan]    Modelo: {model_name}[/]")
    console.print(f"[cyan]    Embeddings: {embedding_model}[/]")

    return rag_service


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Ejecuta el servidor FastAPI.

    Args:
        host: Host para el servidor
        port: Puerto para el servidor
        reload: Si True, recarga automáticamente en desarrollo
    """
    import uvicorn

    # Inicializar servicio RAG
    rag_service = initialize_rag_service()

    # Importar create_app después de inicializar rag_service
    from src.infrastructure.entrypoints.fastapi_adapter import create_app

    # Crear aplicación
    app = create_app(rag_service)

    # Configurar servidor
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
    )

    server = uvicorn.Server(config)

    # Imprimir información
    console.print("\n[bold cyan]=== SERVIDOR API EJECUTÁNDOSE ===[/]")
    console.print(f"[green]    URL: http://{host}:{port}[/]")
    console.print(f"[green]    Docs: http://{host}:{port}/docs[/]")
    console.print(f"[green]    Redoc: http://{host}:{port}/redoc[/]")
    console.print(f"[green]    Health: http://{host}:{port}/api/v1/health[/]")
    console.print("\n[yellow]Presiona Ctrl+C para detener[/]\n")

    # Ejecutar servidor
    server.run()


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Servidor API REST para sistema RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python run_api.py
    python run_api.py --host 0.0.0.0 --port 8000
    python run_api.py --reload  # Desarrollo (auto-reload)

Endpoints:
    GET  /api/v1/health          - Health check
    GET  /api/v1/metrics         - Métricas
    POST /api/v1/query           - Consulta RAG
    POST /api/v1/query/stream    - Consulta streaming
    POST /api/v1/ingest/file     - Ingerir archivo
    POST /api/v1/ingest/directory - Ingerir directorio
        """
    )

    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host para el servidor (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Puerto para el servidor (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Auto-recarga en desarrollo"
    )

    args = parser.parse_args()

    try:
        run_server(host=args.host, port=args.port, reload=args.reload)
    except KeyboardInterrupt:
        console.print("\n[yellow]Servidor detenido por el usuario[/]")
    except Exception as e:
        logger.error(f"Error al ejecutar servidor: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
