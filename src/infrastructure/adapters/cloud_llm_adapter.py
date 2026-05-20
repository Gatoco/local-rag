"""
CloudLLMAdapter - Universal adapter for cloud LLM providers.

Supports: OpenAI, Anthropic, Google (Gemini), Groq, MiniMax, DeepSeek.
API keys are read from environment variables (.env file).
"""

import logging
import os
from collections.abc import Generator
from typing import Any, TypedDict

import httpx

logger = logging.getLogger(__name__)

class ProviderConfig(TypedDict):
    api_key_env: str
    base_url: str
    models: list[str]
    default_model: str
    supports_streaming: bool


PROVIDER_CONFIG: dict[str, ProviderConfig] = {
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini",
        "supports_streaming": True,
    },
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-opus-4", "claude-sonnet-4", "claude-haiku-3.5"],
        "default_model": "claude-sonnet-4",
        "supports_streaming": True,
    },
    "google": {
        "api_key_env": "GOOGLE_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        "default_model": "gemini-2.0-flash",
        "supports_streaming": True,
    },
    "groq": {
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "default_model": "llama-3.1-8b-instant",
        "supports_streaming": True,
    },
    "minimax": {
        "api_key_env": "MINIMAX_API_KEY",
        "base_url": "https://api.minimax.io/v1",
        "models": ["MiniMax-M2.7", "MiniMax-M2.7-highspeed", "MiniMax-M2.5", "MiniMax-M2.5-highspeed", "MiniMax-M2.1", "MiniMax-M2.1-highspeed", "MiniMax-M2"],
        "default_model": "MiniMax-M2.7",
        "supports_streaming": True,
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder"],
        "default_model": "deepseek-chat",
        "supports_streaming": True,
    },
}

TIMEOUT_SECONDS = 20


class CloudLLMConfigurationError(Exception):
    """Error de configuración del adapter cloud."""
    pass


class CloudLLMConnectionError(Exception):
    """Error de conexión con el proveedor cloud."""
    pass


class CloudLLMAdapter:
    """
    Adapter universal para proveedores de LLM en la nube.

    Usage:
        adapter = CloudLLMAdapter(provider="openai", model="gpt-4o-mini")
        response = adapter.generate_response("Hello world")

        # Con API key personalizada
        adapter = CloudLLMAdapter(provider="openai", api_key="sk-...", model="gpt-4o")
        response = adapter.generate_response("Hello world")
    """

    def __init__(
        self,
        provider: str,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int = TIMEOUT_SECONDS,
    ):
        """
        Inicializa el adapter cloud.

        Args:
            provider: Nombre del proveedor (openai, anthropic, google, groq, minimax, deepseek)
            model: Modelo específico (None = usa default del proveedor)
            api_key: API key personalizada (None = usa variable de entorno)
            timeout: Timeout en segundos para requests
        """
        self.provider = provider.lower()
        if self.provider not in PROVIDER_CONFIG:
            raise CloudLLMConfigurationError(
                f"Provider '{provider}' no soportado. "
                f"Providers disponibles: {list(PROVIDER_CONFIG.keys())}"
            )

        config = PROVIDER_CONFIG[self.provider]
        self.model = model or config["default_model"]
        self.api_key = api_key or os.environ.get(config["api_key_env"]) or None
        if not self.api_key:
            raise CloudLLMConfigurationError(
                f"API key no encontrada. Configura {config['api_key_env']} en .env "
                f"o pasa api_key directamente."
            )

        self.base_url = config["base_url"]
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def generate_response(self, prompt: str, max_tokens: int | None = None) -> str:
        """Genera respuesta sincronica."""
        tokens = self.generate_stream(prompt, max_tokens)
        return "".join(tokens)

    def generate_stream(
        self, prompt: str, max_tokens: int | None = None
    ) -> Generator[str, None, None]:
        """Genera respuesta en streaming token por token."""
        payload = self._build_payload(prompt, max_tokens)
        headers = self._build_headers()

        try:
            with self._client.stream("POST", f"{self.base_url}/chat/completions", json=payload, headers=headers) as response:
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
            raise CloudLLMConnectionError(
                f"Timeout ({self.timeout}s) conectando a {self.provider}"
            ) from None
        except httpx.HTTPStatusError as e:
            raise CloudLLMConnectionError(
                f"Error HTTP {e.response.status_code} de {self.provider}: {e.response.text[:200]}"
            ) from e
        except Exception as e:
            raise CloudLLMConnectionError(f"Error de conexión con {self.provider}: {e}") from e

    def _build_payload(self, prompt: str, max_tokens: int | None) -> dict[str, Any]:
        """Construye el payload según el provider."""
        common = {
            "model": self.model,
            "stream": True,
            "max_tokens": max_tokens or 512,
        }

        if self.provider == "anthropic":
            return {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens or 512,
                "stream": True,
            }

        return {
            **common,
            "messages": [{"role": "user", "content": prompt}],
        }

    def _build_headers(self) -> dict[str, str]:
        """Construye headers según el provider."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        api_key = self.api_key if self.api_key is not None else ""

        if self.provider == "openai":
            headers["Authorization"] = f"Bearer {api_key}"
        elif self.provider == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        elif self.provider == "google":
            headers["x-goog-api-key"] = api_key
        elif self.provider == "groq":
            headers["Authorization"] = f"Bearer {api_key}"
        elif self.provider == "minimax":
            headers["Authorization"] = f"Bearer {api_key}"
        elif self.provider == "deepseek":
            headers["Authorization"] = f"Bearer {api_key}"

        return headers

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
        """Retorna el adapter mismo (para compatibilidad con LangChain)."""
        return self

    def get_model_info(self) -> dict[str, Any]:
        """Información del modelo."""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key_set": bool(self.api_key),
            "timeout": self.timeout,
        }

    @staticmethod
    def get_available_providers() -> list[str]:
        """Lista de providers disponibles."""
        return list(PROVIDER_CONFIG.keys())

    @staticmethod
    def get_provider_models(provider: str) -> list[str]:
        """Lista de modelos para un provider."""
        provider = provider.lower()
        if provider not in PROVIDER_CONFIG:
            return []
        config = PROVIDER_CONFIG[provider]
        return list(config["models"])

    @classmethod
    def get_default_model(cls, provider: str) -> str | None:
        """Modelo default para un provider."""
        provider = provider.lower()
        if provider not in PROVIDER_CONFIG:
            return None
        config = PROVIDER_CONFIG[provider]
        return str(config["default_model"]) if config["default_model"] else None
