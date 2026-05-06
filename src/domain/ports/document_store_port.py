from abc import ABC, abstractmethod
from typing import Any


class DocumentStorePort(ABC):
    @abstractmethod
    def add_documents(self, documents: list[Any], ids: list[str] = None):
        """Agrega documentos (ya procesados) al almacén vectorial."""
        pass

    @abstractmethod
    def search_similar(self, query: str, k: int = 4) -> list[Any]:
        """Realiza una búsqueda de similitud semántica."""
        pass

    @abstractmethod
    def get_retriever(self, search_kwargs: dict[str, Any] = None) -> Any:
        """Devuelve un objeto 'retriever' compatible con LangChain."""
        pass
