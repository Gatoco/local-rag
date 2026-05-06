"""
OllamaLLMAdapter - Adapter para inferencia local con Ollama.

NOTA: Este adapter es LEGACY. Se recomienda usar LlamaCppLLMAdapter
para mejor rendimiento y sin dependencias externas.

Se mantiene por compatibilidad y como referencia de implementación.
"""

from collections.abc import Generator
from typing import Any

from langchain_ollama import ChatOllama

from src.domain.ports.llm_port import LLMPort


class OllamaLLMAdapter(LLMPort):
    """
    Adapter para Ollama que implementa LLMPort.

    Ventajas:
    - Simple y fácil de usar
    - Auto-download de modelos
    - Gestión automática de memoria

    Desventajas:
    - Requiere proceso externo (ollama serve)
    - Overhead HTTP (~10-15%)
    - Sin streaming nativo en esta implementación
    """

    def __init__(
        self,
        model_name: str = "mistral-nemo",
        temperature: float = 0.1,
        base_url: str = "http://localhost:11434",
        request_timeout: float = 120.0,
    ):
        """
        Inicializa el adapter para Ollama.

        Args:
            model_name: Nombre del modelo en Ollama
            temperature: Creatividad (0.0 = determinista, 1.0 = creativo)
            base_url: URL donde corre Ollama
            request_timeout: Timeout para requests HTTP
        """
        self.model_name = model_name
        self.temperature = temperature
        self.base_url = base_url

        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=base_url,
            timeout=request_timeout,
            keep_alive="5m"
        )

    def generate_response(self, prompt: str, max_tokens: int | None = None) -> str:
        """Genera una respuesta simple."""
        # Nota: Ollama no soporta max_tokens directamente en ChatOllama
        return self.llm.invoke(prompt).content

    def generate_stream(self, prompt: str, max_tokens: int | None = None) -> Generator[str, None, None]:
        """
        Genera respuesta en streaming usando Ollama.

        Yields:
            Tokens generados uno por uno
        """
        for chunk in self.llm.stream(prompt):
            if hasattr(chunk, 'content'):
                yield chunk.content
            elif isinstance(chunk, dict) and 'message' in chunk:
                yield chunk['message'].get('content', '')

    def get_model(self) -> Any:
        """Devuelve la instancia de ChatOllama."""
        return self.llm
