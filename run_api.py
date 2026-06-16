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
from colorama import Fore, Style, init

# Cargar variables de entorno
load_dotenv()

# Inicializar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def initialize_rag_service():
    """Inicializa el servicio RAG para la API."""
    from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
    from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
    from src.infrastructure.adapters.llama_cpp_llm_adapter import LlamaCppLLMAdapter
    from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter
    from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter
    from src.application.services.rag_service import RAGService
    from src.infrastructure.utils.dependency_validator import DependencyValidator, validate_gguf_model

    print(f"{Fore.CYAN}{Style.BRIGHT}=== INICIALIZANDO SERVIDOR API RAG ==={Style.RESET_ALL}")

    # Validar dependencias
    validator = DependencyValidator()
    if not validator.validate_all():
        print(f"{Fore.RED}[!] Error: Faltan dependencias. Ejecuta: {validator.get_install_command()}{Style.RESET_ALL}")
        sys.exit(1)

    # Configuración
    embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    model_path = os.getenv("LLAMA_CPP_MODEL_PATH", "./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf")
    chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    top_k = int(os.getenv("TOP_K_DOCUMENTS", "4"))
    n_gpu_layers = int(os.getenv("N_GPU_LAYERS", "0"))
    n_ctx = int(os.getenv("N_CTX", "4096"))

    # Validar modelo
    if not os.path.exists(model_path):
        print(f"{Fore.RED}[!] ERROR: Modelo GGUF no encontrado en: {model_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}    Descarga un modelo: python download_model.py{Style.RESET_ALL}")
        sys.exit(1)

    model_info = validate_gguf_model(model_path)
    if not model_info['valid_header']:
        print(f"{Fore.RED}[!] ERROR: Modelo corrupto (header inválido){Style.RESET_ALL}")
        sys.exit(1)
    if not model_info['valid_size']:
        print(f"{Fore.RED}[!] ERROR: Modelo incompleto (< 100MB){Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.YELLOW}[*] Cargando componentes...{Style.RESET_ALL}")

    # Cargar embeddings
    print(f"{Fore.YELLOW}    → Embeddings: {embedding_model}")
    embedding_adapter = HFEmbeddingAdapter(model_name=embedding_model)
    print(f"{Fore.GREEN}    ✓ Embeddings listo.{Style.RESET_ALL}")

    # Cargar LLM
    model_name = os.path.basename(model_path)
    gpu_info = f"(GPU: {n_gpu_layers} capas)" if n_gpu_layers > 0 else "(CPU)"
    print(f"{Fore.YELLOW}    → LLM: {model_name} {gpu_info}")
    llm_adapter = LlamaCppLLMAdapter(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )
    print(f"{Fore.GREEN}    ✓ LLM listo.{Style.RESET_ALL}")

    # Cargar loader
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
    loader_adapter = LangChainLoaderAdapter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Cargar ChromaDB
    print(f"{Fore.YELLOW}    → ChromaDB: {chroma_db_path}")
    doc_store_adapter = ChromaDBAdapter(
        embedding_port=embedding_adapter,
        persist_directory=chroma_db_path
    )
    print(f"{Fore.GREEN}    ✓ ChromaDB listo.{Style.RESET_ALL}")

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

    print(f"{Fore.GREEN}[+] SISTEMA RAG OPERATIVO{Style.RESET_ALL}")
    print(f"{Fore.CYAN}    Modelo: {model_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}    Embeddings: {embedding_model}{Style.RESET_ALL}")

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
    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== SERVIDOR API EJECUTÁNDOSE ==={Style.RESET_ALL}")
    print(f"{Fore.GREEN}    URL: http://{host}:{port}")
    print(f"{Fore.GREEN}    Docs: http://{host}:{port}/docs")
    print(f"{Fore.GREEN}    Redoc: http://{host}:{port}/redoc")
    print(f"{Fore.GREEN}    Health: http://{host}:{port}/api/v1/health{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Presiona Ctrl+C para detener{Style.RESET_ALL}\n")

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
        print(f"\n{Fore.YELLOW}Servidor detenido por el usuario{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Error al ejecutar servidor: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
