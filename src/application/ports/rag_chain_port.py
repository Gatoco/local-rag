"""
Puerto (interfaz) para la cadena RAG - Define el contrato para la orquestación RAG.

Este puerto sigue el principio de inversión de dependencias:
- La lógica de negocio (RAGService) depende de esta abstracción
- Los adapters concretos (LangChain, implementación nativa, etc.) implementan esta interfaz

Propósito:
- Desacoplar RAGService de LangChain directamente
- Permitir migrar a otra librería (LlamaIndex, Haystack) sin cambiar RAGService
- Facilitar testing con mocks
"""

from abc import ABC, abstractmethod
from typing import Any

from src.domain.models import Document


class RAGChainPort(ABC):
    """
    Contrato para cadenas de orquestación RAG.

    Esta interfaz abstrae la implementación específica de la cadena RAG,
    permitiendo intercambiar LangChain por otra librería sin modificar
    la lógica de negocio.

    Responsabilidades:
    - Combinar documentos recuperados con prompt
    - Invocar LLM con contexto
    - Retornar respuesta estructurada

    Example de implementación:
        class LangChainRAGAdapter(RAGChainPort):
            def __init__(self, llm, retriever, prompt_template):
                self.chain = create_retrieval_chain(...)

            def invoke(self, input_text: str) -> Dict[str, Any]:
                return self.chain.invoke({"input": input_text})
    """

    @abstractmethod
    def invoke(self, input_text: str) -> dict[str, Any]:
        """
        Ejecuta la cadena RAG con el input dado.

        Args:
            input_text: El texto de entrada (pregunta del usuario)

        Returns:
            Diccionario con:
                - answer: La respuesta generada por el LLM
                - context: Lista de documentos recuperados (u otro formato)
                - metadata: Información adicional (opcional)

        Raises:
            Exception: Si hay un error en la ejecución de la cadena
        """
        pass

    @abstractmethod
    def get_retriever(self) -> Any:
        """
        Obtiene el retriever subyacente.

        Returns:
            El objeto retriever usado para búsqueda vectorial

        Note:
            Esto permite acceso directo al retriever para operaciones avanzadas
            como configuración dinámica de top_k.
        """
        pass

    @abstractmethod
    def update_retriever_config(self, search_kwargs: dict[str, Any]) -> None:
        """
        Actualiza la configuración del retriever.

        Args:
            search_kwargs: Parámetros de búsqueda (ej: {"k": 4})

        Note:
            Útil para cambiar top_k dinámicamente sin recrear la cadena.
        """
        pass


class DocumentCombinerPort(ABC):
    """
    Contrato para combinadores de documentos.

    Esta interfaz abstrae cómo se combinan los documentos recuperados
    con el prompt para el LLM.

    Responsabilidades:
    - Formatear documentos en string
    - Aplicar template al contexto
    - Preparar input para el LLM
    """

    @abstractmethod
    def combine(self, documents: list[Document], input_text: str) -> str:
        """
        Combina documentos con el input en un prompt formateado.

        Args:
            documents: Lista de documentos recuperados
            input_text: La pregunta del usuario

        Returns:
            Prompt formateado listo para enviar al LLM
        """
        pass
