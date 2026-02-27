# src/application/ports/rag_port.py
# Propósito: Define el puerto de entrada principal para interactuar con el sistema RAG.

from abc import ABC, abstractmethod
from typing import List
from src.domain.models import Answer, Document

class RagPort(ABC):
    # Propósito: Interfaz que expone las funcionalidades principales del sistema RAG.
    @abstractmethod
    def query(self, question: str) -> Answer:
        # Propósito: Consulta el sistema RAG con una pregunta y devuelve una Answer.
        pass

    @abstractmethod
    def ingest_documents(self, file_paths: List[str]) -> List[str]:
        # Propósito: Ingesta documentos de rutas de archivo específicas en el sistema RAG.
        # Retorna una lista de IDs para los documentos ingeridos.
        pass
