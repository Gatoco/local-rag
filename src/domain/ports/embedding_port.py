# src/domain/ports/embedding_port.py
# Propósito: Define el puerto de salida para la generación de incrustaciones (embeddings).

from abc import ABC, abstractmethod
from typing import List

class EmbeddingPort(ABC):
    # Propósito: Interfaz para generar incrustaciones a partir de texto.
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Propósito: Genera incrustaciones para una lista de textos.
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        # Propósito: Genera una incrustación para un solo texto de consulta.
        pass
