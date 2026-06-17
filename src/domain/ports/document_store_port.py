from abc import ABC, abstractmethod
from typing import Any


class DocumentStorePort(ABC):
    @abstractmethod
    def add_documents(self, documents: list[Any], ids: list[str] | None = None):
        """Agrega documentos (ya procesados) al almacén vectorial."""
        pass

    @abstractmethod
    def search_similar(self, query: str, k: int = 4) -> list[Any]:
        """Realiza una búsqueda de similitud semántica."""
        pass

    @abstractmethod
    def get_retriever(self, search_kwargs: dict[str, Any] | None = None) -> Any:
        """Devuelve un objeto 'retriever' compatible con LangChain."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Retorna el numero de documentos en el almacen vectorial."""
        pass

    @abstractmethod
    def list_documents(self, limit: int = 20, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        """
        Lista documentos con paginación.

        Args:
            limit: Máximo de documentos a retornar
            offset: Offset para paginación

        Returns:
            Tuple de (lista de documentos con id y metadata, total count)
        """
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        Elimina un documento por ID.

        Args:
            document_id: ID del documento a eliminar

        Returns:
            True si se elimino, False si no existe
        """
        pass

    @abstractmethod
    def query_with_embeddings(
        self,
        query_embeddings: list[float],
        k: int = 4,
        include_documents: bool = True,
        include_metadatas: bool = True,
    ) -> dict[str, Any]:
        """
        Busca documentos usando embeddings pre-computados.

        Args:
            query_embeddings: Embeddings de la query
            k: Numero de documentos a recuperar
            include_documents: Incluir textos en resultados
            include_metadatas: Incluir metadatos en resultados

        Returns:
            Dict con 'documents', 'metadatas', 'ids', 'distances'
        """
        pass
