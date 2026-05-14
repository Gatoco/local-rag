"""
LMStudioLLMAdapter - Adapter para LM Studio (ejecución local de modelos).

LM Studio es un servidor local que expone endpoints estilo OpenAI.
Este adapter se conecta a él para ejecutar modelos locales.
"""

import logging
from collections.abc import Generator
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LMStudioConfigurationError(Exception):
    """Error de configuración de LM Studio."""
    pass


class LMStudioConnectionError(Exception):
    """Error de conexión con LM Studio."""
    pass


class LMStudioLLMAdapter:
    """
    Adapter para LM Studio.

    LM Studio corre localmente y expone una API compatible con OpenAI.
    Por default se conecta a http://localhost:1234/v1.

    Usage:
        adapter = LMStudioLLMAdapter()
        response = adapter.generate_response("Hello")
    """

    DEFAULT_BASE_URL = "http://localhost:1234/v1"
    TIMEOUT = 60

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 512,
    ):
        """
        Inicializa el adapter de LM Studio.

        Args:
            base_url: URL del servidor LM Studio (default: http://localhost:1234/v1)
            model: Nombre del modelo cargado en LM Studio
            temperature: Temperatura de generación
            max_tokens: Máximo de tokens a generar
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = httpx.Client(timeout=self.TIMEOUT)
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verifica que LM Studio esté corriendo."""
        try:
            response = self._client.get(self.base_url.replace("/v1", "/models"))
            if response.status_code != 200:
                raise LMStudioConnectionError(
                    f"LM Studio responded with status {response.status_code}. "
                    f"Ensure LM Studio is running at {self.base_url}"
                )
        except httpx.ConnectError:
            raise LMStudioConnectionError(
                f"Cannot connect to LM Studio at {self.base_url}. "
                f"Start LM Studio and ensure the local server is enabled."
            ) from None

    def generate_response(self, prompt: str, max_tokens: int | None = None) -> str:
        """Genera respuesta sincronica."""
        tokens = self.generate_stream(prompt, max_tokens)
        return "".join(tokens)

    def generate_stream(
        self, prompt: str, max_tokens: int | None = None
    ) -> Generator[str, None, None]:
        """Genera respuesta en streaming."""
        payload = {
            "model": self.model or "local-model",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "temperature": self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        try:
            with self._client.stream("POST", f"{self.base_url}/chat/completions", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            return
                        token = self._parse_sse_token(data)
                        if token:
                            yield token
        except httpx.TimeoutException:
            raise LMStudioConnectionError(f"Timeout connecting to LM Studio at {self.base_url}") from None
        except Exception as e:
            raise LMStudioConnectionError(f"Error communicating with LM Studio: {e}") from e

    def _parse_sse_token(self, data: str) -> str | None:
        """Parsea token de SSE data."""
        try:
            import json
            parsed = json.loads(data)
            choices = parsed.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                text = delta.get("text")
                if content is not None:
                    return str(content)
                if text is not None:
                    return str(text)
        except Exception:
            pass
        return None

    def get_model(self) -> Any:
        """Retorna el adapter mismo."""
        return self

    def get_model_info(self) -> dict[str, Any]:
        """Información del modelo."""
        return {
            "provider": "lmstudio",
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
        }

    @staticmethod
    def get_available_providers() -> list[str]:
        """Lista de providers disponibles (solo lmstudio)."""
        return ["lmstudio"]

    @staticmethod
    def get_provider_models(provider: str) -> list[str]:
        """LM Studio usa modelos locales, no hay lista predefinida."""
        return []
