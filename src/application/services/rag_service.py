# src/application/services/rag_service.py
# Propósito: Implementa la lógica central del sistema RAG, orquestando el flujo de trabajo.

from typing import List
from src.application.ports.rag_port import RagPort
from src.domain.models import Document, Query, Answer
from src.domain.ports.document_store_port import DocumentStorePort
from src.domain.ports.embedding_port import EmbeddingPort
from src.domain.ports.llm_port import LLMPort
from src.domain.ports.document_loader_port import DocumentLoaderPort

class RAGService(RagPort):
    # Propósito: Servicio de aplicación que coordina las operaciones RAG.
    def __init__(
        self,
        document_store: DocumentStorePort,
        embedding_model: EmbeddingPort,
        llm_model: LLMPort,
        document_loader: DocumentLoaderPort
    ):
        # Propósito: Inicializa el servicio RAG con las implementaciones de los puertos necesarios.
        # Guardar las instancias de los puertos inyectados.
        pass

    def ingest_documents(self, file_paths: List[str]) -> List[str]:
        # Propósito: Procesa una lista de rutas de archivo para cargar, dividir y almacenar documentos.
        # Inicializar lista para almacenar IDs de documentos.
        # Iterar sobre cada file_path:
            # 1. Cargar documentos usando self.document_loader.load_documents.
            # 2. Dividir documentos en chunks usando self.document_loader.split_documents.
            # 3. Añadir documentos divididos al store usando self.document_store.add_documents.
            #    (El adaptador del store se encargará de las embeddings).
            # 4. Extender la lista de IDs con los IDs resultantes.
        # Retornar la lista total de IDs.
        pass

    def query(self, question: str) -> Answer:
        # Propósito: Procesa una pregunta del usuario, busca documentos relevantes y genera una respuesta.
        # 1. Embed la consulta usando self.embedding_model.embed_query.
        # 2. Buscar documentos relevantes usando self.document_store.search_documents con la incrustación de la consulta.
        # 3. Construir el prompt para el LLM, incluyendo el contexto de los documentos relevantes.
        # 4. Generar respuesta usando self.llm_model.generate_answer con el prompt construido.
        # 5. Retornar un objeto Answer con el texto de la respuesta y los documentos fuente.
        pass
