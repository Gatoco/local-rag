# main.py
# Propósito: Punto de entrada principal de la aplicación RAG local.
# Configura la arquitectura hexagonal y lanza el chat interactivo.
# NOTA: Usa llama.cpp para inferencia local SIN proceso externo

import sys
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Añadir el directorio 'src' al path de Python para permitir importaciones relativas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Configurar logging primero
from src.infrastructure.utils.logging_config import setup_logging, get_logger
setup_logging(level="INFO", log_file="rag.log", log_dir="./logs")

logger = get_logger(__name__)

from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
from src.infrastructure.adapters.llama_cpp_llm_adapter import LlamaCppLLMAdapter
from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter
from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter
from src.application.services.rag_service import RAGService
from src.infrastructure.entrypoints.cli_adapter import CLIAdapter
from src.infrastructure.utils.dependency_validator import DependencyValidator, validate_gguf_model

# Inicializar colores para la terminal
init(autoreset=True)

def main():
    load_dotenv()

    print(f"{Fore.CYAN}{Style.BRIGHT}=== SISTEMA RAG LOCAL (llama.cpp) ==={Style.RESET_ALL}")
    logger.info("Iniciando sistema RAG...")

    # --- 0. Validación de dependencias ---
    logger.debug("Validando dependencias...")
    validator = DependencyValidator()
    if not validator.validate_all():
        print(f"{Fore.RED}[!] Error: Faltan dependencias. Ejecuta: {validator.get_install_command()}{Style.RESET_ALL}")
        logger.error("Validación de dependencias fallida")
        return

    # --- 1. Configuración ---
    embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    model_path = os.getenv("LLAMA_CPP_MODEL_PATH", "./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf")
    chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    default_docs_path = os.getenv("DOCS_PATH", "./docs_to_ingest")
    top_k = int(os.getenv("TOP_K_DOCUMENTS", "4"))
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
    n_gpu_layers = int(os.getenv("N_GPU_LAYERS", "0"))
    n_ctx = int(os.getenv("N_CTX", "4096"))

    logger.info(f"Configuración: model={model_path}, ctx={n_ctx}, gpu_layers={n_gpu_layers}")

    # --- 2. Validación de dependencias ---
    print(f"{Fore.YELLOW}[*] Cargando motores de IA locales...")

    # Validar modelo GGUF
    if not os.path.exists(model_path):
        print(f"{Fore.RED}[!] CRÍTICO: Modelo GGUF no encontrado en: {model_path}")
        print(f"{Fore.YELLOW}    Descarga un modelo:")
        print(f"    python download_model.py")
        print(f"    ")
        print(f"    O manualmente:")
        print(f"    wget -O {model_path} \\")
        print(f"      https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf")
        logger.error(f"Modelo no encontrado: {model_path}")
        return

    # Validar modelo GGUF (header y tamaño)
    model_info = validate_gguf_model(model_path)
    if not model_info['valid_header']:
        print(f"{Fore.RED}[!] ERROR: El modelo parece corrupto (header inválido){Style.RESET_ALL}")
        logger.error(f"Modelo corrupto: {model_path}")
        return
    if not model_info['valid_size']:
        print(f"{Fore.RED}[!] ERROR: El modelo es demasiado pequeño (< 100MB){Style.RESET_ALL}")
        logger.error(f"Modelo incompleto: {model_info['size_mb']:.1f} MB")
        return

    logger.info(f"Modelo validado: {model_info['size_mb']:.1f} MB")
    
    # --- 3. Inicialización de Infraestructura (Adaptadores) ---
    try:
        print(f"{Fore.YELLOW}    → Cargando embeddings (primera ejecución: ~1 min)...")
        logger.debug("Cargando embeddings...")
        embedding_adapter = HFEmbeddingAdapter(model_name=embedding_model)
        print(f"{Fore.GREEN}    ✓ Embeddings listo.")
        logger.info("Embeddings cargados: %s", embedding_model)
    except Exception as e:
        print(f"{Fore.RED}[!] Error al cargar embeddings: {e}{Style.RESET_ALL}")
        logger.error("Error en embeddings: %s", e, exc_info=True)
        return

    try:
        model_name = os.path.basename(model_path)
        gpu_info = f"(GPU: {n_gpu_layers} capas)" if n_gpu_layers > 0 else "(CPU)"
        print(f"{Fore.YELLOW}    → Inicializando LLM llama.cpp {model_name} {gpu_info}...")
        logger.debug("Cargando LLM: %s, ctx=%d, gpu_layers=%d", model_path, n_ctx, n_gpu_layers)
        llm_adapter = LlamaCppLLMAdapter(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )
        print(f"{Fore.GREEN}    ✓ LLM listo.")
        logger.info("LLM cargado: %s", model_name)
    except Exception as e:
        print(f"{Fore.RED}[!] Error al inicializar LLM: {e}{Style.RESET_ALL}")
        logger.error("Error en LLM: %s", e, exc_info=True)
        return

    loader_adapter = LangChainLoaderAdapter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Cargar ChromaDB
    try:
        print(f"{Fore.YELLOW}    → Inicializando base de datos vectorial (Chroma)...")
        doc_store_adapter = ChromaDBAdapter(
            embedding_port=embedding_adapter,
            persist_directory=chroma_db_path
        )
        print(f"{Fore.GREEN}    ✓ ChromaDB listo.")
        logger.info("ChromaDB inicializado: %s", chroma_db_path)
    except Exception as e:
        print(f"{Fore.RED}[!] Error al inicializar ChromaDB: {e}{Style.RESET_ALL}")
        logger.error("Error en ChromaDB: %s", e, exc_info=True)
        return

    # Cargar prompt template desde archivo (o usar default)
    prompt_template_path = os.getenv("PROMPT_TEMPLATE_PATH", "./prompts/rag_prompt.txt")
    try:
        if os.path.exists(prompt_template_path):
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            logger.info(f"Prompt template cargado desde: {prompt_template_path}")
            print(f"{Fore.GREEN}    ✓ Prompt template cargado desde archivo.")
        else:
            # Fallback a prompt por defecto
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
            logger.warning(f"Prompt template no encontrado en {prompt_template_path}, usando default")
            print(f"{Fore.YELLOW}    ⚠ Prompt template no encontrado, usando default.")
    except Exception as e:
        logger.error(f"Error cargando prompt template: {e}")
        print(f"{Fore.YELLOW}    ⚠ Error cargando prompt template, usando default.")
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

    try:
        logger.debug("Creando LangChainRAGAdapter...")
        rag_chain = LangChainRAGAdapter(
            llm_adapter=llm_adapter,
            doc_store=doc_store_adapter,
            prompt_template=prompt_template,
            top_k=top_k
        )
        logger.info("LangChainRAGAdapter creado exitosamente")
    except Exception as e:
        print(f"{Fore.RED}[!] Error al crear LangChainRAGAdapter: {e}{Style.RESET_ALL}")
        logger.error("Error en LangChainRAGAdapter: %s", e, exc_info=True)
        return

    try:
        rag_service = RAGService(
            chain=rag_chain,
            doc_store_adapter=doc_store_adapter,
            loader_adapter=loader_adapter,
            top_k=top_k
        )
        print(f"{Fore.GREEN}[+] SISTEMA RAG OPERATIVO. Modelo: {model_name}{Style.RESET_ALL}")
        logger.info("RAGService inicializado")
    except Exception as e:
        print(f"{Fore.RED}[!] Error al inicializar RAGService: {e}{Style.RESET_ALL}")
        logger.error("Error en RAGService: %s", e, exc_info=True)
        return

    # --- 4. Ingesta inicial opcional ---
    if os.path.isdir(default_docs_path) and os.listdir(default_docs_path):
        print(f"{Fore.YELLOW}[*] Ingesta inicial desde: {default_docs_path}")
        try:
            rag_service.ingest_directory(default_docs_path)
            print(f"{Fore.GREEN}[+] Ingesta completada.")
        except Exception as exc:
            print(f"{Fore.RED}[!] La ingesta inicial falló: {exc}")
    else:
        print(f"{Fore.YELLOW}[*] No hay documentos en {default_docs_path}.")
        print(f"{Fore.WHITE}    Puedes cargarlos con: ingest-dir <ruta>{Style.RESET_ALL}")

    # --- 5. CLI Interactiva ---
    print(f"\n{Fore.CYAN}{Style.BRIGHT}--- CLI RAG INTERACTIVA ---{Style.RESET_ALL}")
    cli = CLIAdapter(rag_service)
    cli.run()

if __name__ == "__main__":
    main()
