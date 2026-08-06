from abc import ABC, abstractmethod
from typing import Any


class EmbeddingPort(ABC):
    @abstractmethod
    def get_embeddings_model(self) -> Any:
        """Devuelve el modelo de embeddings para ser usado por el almacén vectorial."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Convierte una cadena de texto en un vector numérico."""
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Convierte múltiples textos en vectores numéricos (batch)."""
        pass
