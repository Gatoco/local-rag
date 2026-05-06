from abc import ABC, abstractmethod
from typing import Any


class RAGPort(ABC):
    @abstractmethod
    def ingest_document(self, file_path: str) -> None:
        """Procesa e indexa un documento individual."""
        pass

    @abstractmethod
    def ingest_directory(self, dir_path: str) -> None:
        """Procesa e indexa todos los documentos de un directorio."""
        pass

    @abstractmethod
    def ask(self, question: str) -> dict[str, Any]:
        """Pregunta al sistema basándose en los documentos indexados."""
        pass
