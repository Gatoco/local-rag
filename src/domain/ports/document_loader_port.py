# src/domain/ports/document_loader_port.py
# Propósito: Define el puerto de salida para la carga y división de documentos.

from abc import ABC, abstractmethod
from typing import List
from src.domain.models import Document

class DocumentLoaderPort(ABC):
    # Propósito: Interfaz para cargar y dividir documentos.
    @abstractmethod
    def load_documents(self, file_path: str) -> List[Document]:
        # Propósito: Carga documentos desde una ruta de archivo especificada.
        pass

    @abstractmethod
    def split_documents(self, documents: List[Document]) -> List[Document]:
        # Propósito: Divide una lista de documentos en trozos más pequeños y procesables.
        pass
