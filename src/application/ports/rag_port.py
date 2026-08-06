from abc import ABC, abstractmethod
from collections.abc import Generator
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

    @abstractmethod
    def ask_stream(
        self, question: str, provider: str | None = None, max_tokens: int | None = None
    ) -> Generator[str, None, None]:
        """Pregunta al sistema con streaming token por token."""
        pass

    @abstractmethod
    def get_document_count(self) -> int:
        """Retorna el número de documentos en el índice."""
        pass
