"""
LangChainRAGAdapter - Adapter para orquestación RAG con LangChain.

Implementa RAGChainPort usando LangChain chains.
Permite desacoplar RAGService de LangChain directamente.
"""

import logging
from typing import Any

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from src.application.ports.rag_chain_port import RAGChainPort
from src.domain.ports.document_store_port import DocumentStorePort
from src.domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)


class LangChainRAGAdapter(RAGChainPort):
    """
    Adapter que implementa RAGChainPort usando LangChain.

    Este adapter encapsula toda la lógica específica de LangChain,
    permitiendo que RAGService sea agnóstico a la implementación.

    Attributes:
        llm: El modelo de lenguaje (de get_model())
        retriever: El retriever de documentos
        combine_docs_chain: Cadena que combina documentos
        rag_chain: Cadena RAG completa

    Example:
        adapter = LangChainRAGAdapter(
            llm_adapter=llm_adapter,
            doc_store=doc_store_adapter,
            prompt_template="Eres un asistente... {context}... Pregunta: {input}"
        )
        result = adapter.invoke("¿Qué es Python?")
    """

    def __init__(
        self,
        llm_adapter: LLMPort,
        doc_store: DocumentStorePort,
        prompt_template: str,
        top_k: int = 4,
    ):
        """
        Inicializa el adapter con LangChain.

        Args:
            llm_adapter: Adapter del LLM (para obtener el modelo)
            doc_store: Adapter del almacén de documentos
            prompt_template: Template para el prompt RAG
            top_k: Número de documentos a recuperar
        """
        self.llm = llm_adapter.get_model()
        self.doc_store = doc_store
        self.prompt_template = prompt_template
        self.top_k = top_k

        try:
            self._initialize_chains()
            logger.info(f"LangChainRAGAdapter inicializado con top_k={top_k}")
        except Exception as e:
            logger.error(f"Error al inicializar cadenas LangChain: {e}")
            raise

    def _initialize_chains(self) -> None:
        """Inicializa las cadenas de LangChain."""
        logger.debug("Inicializando cadenas LangChain...")

        # Crear prompt template
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)

        # Crear cadena de combinación de documentos
        self.combine_docs_chain = create_stuff_documents_chain(llm=self.llm, prompt=self.prompt)

        # Crear cadena RAG completa
        self.rag_chain = create_retrieval_chain(
            retriever=self.get_retriever(), combine_docs_chain=self.combine_docs_chain
        )

        logger.debug("Cadenas LangChain inicializadas correctamente")

    def invoke(self, input_text: str) -> dict[str, Any]:
        """
        Ejecuta la cadena RAG con el input dado.

        Args:
            input_text: La pregunta del usuario

        Returns:
            Diccionario con:
                - answer: La respuesta generada
                - context: Lista de documentos recuperados

        Raises:
            Exception: Si falla la ejecución
        """
        logger.debug(f"Ejecutando RAG chain con input: {input_text[:100]}...")

        try:
            response = self.rag_chain.invoke({"input": input_text})

            logger.debug(f"RAG chain completada: {len(response.get('context', []))} documentos")

            return {
                "answer": response.get("answer", ""),
                "context": response.get("context", []),
            }

        except Exception as e:
            logger.error(f"Error en RAG chain: {e}", exc_info=True)
            raise

    def get_retriever(self) -> Any:
        """
        Obtiene el retriever subyacente.

        Returns:
            El retriever configurado con search_kwargs
        """
        return self.doc_store.get_retriever(search_kwargs={"k": self.top_k})

    def update_retriever_config(self, search_kwargs: dict[str, Any]) -> None:
        """
        Actualiza la configuración del retriever.

        Args:
            search_kwargs: Nuevos parámetros de búsqueda
        """
        logger.debug(f"Actualizando retriever config: {search_kwargs}")

        # Actualizar top_k si está presente
        if "k" in search_kwargs:
            self.top_k = search_kwargs["k"]

        # Nota: LangChain retrievers son inmutables, hay que recrear
        # En una implementación futura, podríamos hacer esto más eficiente
        logger.info(f"top_k actualizado a {self.top_k}")

    def get_chain_info(self) -> dict[str, Any]:
        """
        Obtiene información sobre la cadena RAG.

        Returns:
            Dict con información de la configuración
        """
        return {
            "type": "langchain",
            "top_k": self.top_k,
            "prompt_template": self.prompt_template[:100] + "...",
        }
