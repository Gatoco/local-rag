# src/domain/ports/document_store_port.py
# Propósito: Define el puerto de salida para la interacción con el almacén de documentos.

from abc import ABC, abstractmethod
from typing import List, Tuple
from src.domain.models import Document

class DocumentStorePort(ABC):
    # Propósito: Interfaz para interactuar con un almacén de documentos (por ejemplo, una base de datos vectorial).
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        # Propósito: Añade documentos al almacén y devuelve sus IDs.
        pass

    @abstractmethod
    def search_documents(self, query_embedding: List[float], k: int = 4) -> List[Document]:
        # Propósito: Busca documentos relevantes basados en una incrustación de consulta.
        pass

    @abstractmethod
    def delete_document(self, document_id: str):
        # Propósito: Elimina un documento por su ID.
        pass
