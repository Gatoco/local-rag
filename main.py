# main.py
# Propósito: Punto de entrada principal de la aplicación RAG.
# Configura la arquitectura hexagonal y lanza la interfaz de línea de comandos.

import sys
import os

# Propósito: Añadir el directorio 'src' al path de Python para permitir la importación de módulos internos.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
from src.infrastructure.adapters.ollama_llm_adapter import OllamaLLMAdapter
from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter
from src.application.services.rag_service import RAGService
from src.infrastructure.entrypoints.cli_adapter import CLIAdapter

def main():
    # Propósito: Configura todos los componentes de la aplicación y los interconecta.
    # Imprimir mensaje de configuración.

    # --- 1. Inicializar Adapters (Implementaciones de los puertos de salida) ---
    # Propósito: Crear instancias de los adaptadores que conectan el dominio con tecnologías externas.
    # Inicializar el adaptador de embeddings (ej. HFEmbeddingAdapter).
    # Inicializar el adaptador LLM (ej. OllamaLLMAdapter).
    # Inicializar el adaptador de carga de documentos (ej. LangChainLoaderAdapter).
    # Inicializar el adaptador de la base de datos de documentos (ej. ChromaDBAdapter),
    # inyectándole el adaptador de embeddings si es necesario.
    
    # --- 2. Inicializar el Servicio de Aplicación (Core Logic) ---
    # Propósito: Crear el servicio RAG inyectándole sus dependencias (las implementaciones de los puertos).
    # Crear una instancia de RAGService, pasándole los adaptadores inicializados.

    # --- 3. Inicializar el Adaptador de Entrada (CLI) ---
    # Propósito: Crear el adaptador CLI inyectándole el RagService como su dependencia.
    # Crear una instancia de CLIAdapter.

    # Imprimir mensaje de finalización de configuración.
    # Iniciar la ejecución del adaptador CLI.
    pass

if __name__ == "__main__":
    # Propósito: Asegura que la función main() se ejecute cuando el script es el programa principal.
    main()
