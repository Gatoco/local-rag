import os
import pytest

try:
    from src.infrastructure.adapters.llama_cpp_llm_adapter import LlamaCppLLMAdapter
except ImportError:
    LlamaCppLLMAdapter = None

from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter
from src.application.services.rag_service import RAGService

def test_full_rag_flow_integration():
    """
    Verifica que el sistema puede ingestar un archivo TXT,
    recuperar el contexto y generar una respuesta coherente.
    NOTA: Este test requiere un modelo GGUF disponible.
    """
    if LlamaCppLLMAdapter is None:
        pytest.skip("llama_cpp no instalado. Skip test de integración.")

    # 1. Setup con base de datos temporal para el test
    test_db_dir = "./test_chroma_db"
    test_file = "test_data.txt"

    # Obtener ruta del modelo desde variables de entorno o usar default
    model_path = os.getenv("LLAMA_CPP_MODEL_PATH", "./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf")

    # Skip si no hay modelo disponible (test opcional)
    if not os.path.exists(model_path):
        pytest.skip("Modelo GGUF no disponible. Skip test de integración.")

    # Creamos un archivo de prueba con información específica
    with open(test_file, "w") as f:
        f.write("El código secreto del proyecto local-rag es: ALPHA-99-ZULU.\n")
        f.write("La arquitectura utilizada es Hexagonal con LangChain y llama.cpp.")

    try:
        # Inicialización
        llm = LlamaCppLLMAdapter(model_path=model_path, n_ctx=4096)
        embeddings = HFEmbeddingAdapter()
        store = ChromaDBAdapter(embedding_port=embeddings, persist_directory=test_db_dir)
        loader = LangChainLoaderAdapter()

        service = RAGService(llm, store, loader)

        # 2. Ingesta
        service.ingest_document(test_file)

        # 3. Consulta
        query = "¿Cuál es el código secreto del proyecto?"
        result = service.ask(query)

        # 4. Validaciones
        assert "ALPHA-99-ZULU" in result["answer"].upper()
        assert len(result["source_documents"]) > 0
        print("\n[V] Test de Integración RAG: PASADO")

    finally:
        # Limpieza de archivos temporales
        if os.path.exists(test_file):
            os.remove(test_file)
        # Nota: En producción usaríamos una librería de cleanup para la DB temporalEso no es correcto. Debido a que el estudio debe mostrar datos de bienestar por sucursal, los dos campos a incluir son la sucursal y la membresía de un gimnasio. El campo de la sucursal contiene los datos relevantes para la oficina de la marca específica y el campo Membresía del gimnasio contiene datos relevantes para la salud y el bienestar. Los otros campos no son relevantes porque no proporcionan información sobre el bienestar ni ayudan a identificar la ubicación de la sucursal. Seleccione Reiniciar y envíe las respuestas correctas.



