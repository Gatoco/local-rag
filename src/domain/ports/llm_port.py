"""
Puerto (interfaz) para el LLM - Define el contrato que deben cumplir todos los adapters.

Este puerto sigue el principio de inversión de dependencias:
- La lógica de negocio (RAGService) depende de esta abstracción
- Los adapters concretos (Ollama, LlamaCpp) implementan esta interfaz
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any


class LLMPort(ABC):
    """
    Contrato para proveedores de LLM.

    Permite intercambiar el motor de inferencia (Ollama, llama.cpp, OpenAI, etc.)
    sin modificar la lógica de negocio del sistema RAG.

    Ejemplo de uso:
        class OllamaLLMAdapter(LLMPort):
            def generate_response(self, prompt: str) -> str:
                ...

            def get_model(self) -> Any:
                ...
    """

    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int | None = None) -> str:
        """
        Genera una respuesta de texto basada en un prompt.

        Args:
            prompt: El prompt de entrada para el LLM
            max_tokens: Máximo de tokens a generar (None = usa el default del modelo)

        Returns:
            La respuesta generada por el LLM como string

        Raises:
            Exception: Si hay un error en la generación
        """
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, max_tokens: int | None = None) -> Generator[str, None, None]:
        """
        Genera una respuesta en streaming (token por token).

        Útil para mostrar progreso al usuario en tiempo real.

        Args:
            prompt: El prompt de entrada para el LLM
            max_tokens: Máximo de tokens a generar

        Yields:
            Tokens generados uno por uno

        Raises:
            Exception: Si hay un error en la generación
        """
        pass

    @abstractmethod
    def get_model(self) -> Any:
        """
        Devuelve el objeto del modelo subyacente.

        Esto permite integración con LangChain y otras librerías que requieren
        acceso directo al objeto del modelo.

        Returns:
            La instancia del modelo (ej: ChatOllama, Llama, etc.)

        Note:
            Esta es una "fuga de abstracción" necesaria para compatibilidad.
            El código de dominio no debería depender del tipo retornado.
        """
        pass
