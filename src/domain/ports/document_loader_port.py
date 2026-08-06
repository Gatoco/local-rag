from abc import ABC, abstractmethod
from typing import Any


class DocumentLoaderPort(ABC):
    @abstractmethod
    def load_and_split(self, file_path: str) -> list[Any]:
        """Carga un archivo y lo divide en fragmentos (chunks)."""
        pass

    @abstractmethod
    def load_directory(self, dir_path: str) -> list[Any]:
        """Carga todos los archivos de un directorio y los divide."""
        pass
