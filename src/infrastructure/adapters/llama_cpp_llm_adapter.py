"""
LlamaCppLLMAdapter - Adapter para inferencia local con llama.cpp

Este adapter reemplaza la dependencia externa de Ollama, ejecutando modelos GGUF
directamente en el proceso Python sin necesidad de servidores HTTP externos.

Características mejoradas:
- Streaming de tokens en tiempo real
- Configuración flexible de parámetros
- Logging estructurado
- Validación robusta de dependencias
- Reintentos automáticos en carga de modelo
"""

import logging
import os
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

from llama_cpp import Llama

from src.domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)


class LlamaCppConfigurationError(Exception):
    """Excepción para errores de configuración del adapter."""
    pass


class LlamaCppModelLoadError(Exception):
    """Excepción para errores en carga del modelo."""
    pass


class LlamaCppLLMAdapter(LLMPort):
    """
    Adapter para ejecutar LLMs locales usando llama.cpp directamente.
    """

    DEFAULT_STOP_TOKENS = ["</s>", "[INST]", "[/INST]", "User:", "Assistant:"]

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
        temperature: float = 0.1,
        max_tokens: int = 512,
        stop_tokens: list[str] | None = None,
        verbose: bool = False,
        n_batch: int = 512,
        use_mlock: bool = True,
        use_mmap: bool = True,
        n_retry: int = 3,
    ):
        """
        Inicializa el adapter para llama.cpp.

        Args:
            model_path: Ruta al modelo GGUF
            n_ctx: Ventana de contexto máxima (tokens)
            n_threads: Hilos de CPU (None = auto-detectar)
            n_gpu_layers: Capas a acelerar con GPU (0 = solo CPU)
            temperature: Creatividad (0.0 = determinista, 1.0 = creativo)
            max_tokens: Máximo de tokens a generar
            stop_tokens: Tokens para detener generación
            verbose: Mostrar logs de inicialización
            n_batch: Tamaño de batch para procesamiento
            use_mlock: Bloquear en RAM (evita swap)
            use_mmap: Mapeo de memoria (carga rápida)
            n_retry: Reintentos en carga de modelo
        """
        self._validate_model_path(model_path)

        if n_threads is None:
            n_threads = os.cpu_count() or 4

        self.model_path = model_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.stop_tokens = stop_tokens or self.DEFAULT_STOP_TOKENS.copy()
        self.verbose = verbose
        self.n_batch = n_batch

        self.llm = self._load_model_with_retry(n_retry, n_batch, use_mlock, use_mmap)

        logger.info(f"Modelo cargado: {model_path} (ctx={n_ctx}, threads={n_threads})")

    def _validate_model_path(self, model_path: str) -> None:
        """Valida que el modelo existe y es accesible."""
        path = Path(model_path)
        if not path.exists():
            raise LlamaCppConfigurationError(
                f"Modelo GGUF no encontrado en: {model_path}\n"
                f"Descarga un modelo de:\n"
                f"  - https://huggingface.co/TheBloke\n"
                f"  - https://huggingface.co/lmstudio-community\n"
                f"\n"
                f"Ejemplo:\n"
                f"  wget -O {model_path} "
                f"https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/"
                f"resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf"
            )
        if not path.is_file():
            raise LlamaCppConfigurationError(f"La ruta no es un archivo: {model_path}")
        if path.stat().st_size < 100 * 1024 * 1024:  # < 100MB
            raise LlamaCppConfigurationError(
                f"El modelo parece corrupto o incompleto (< 100MB): {model_path}"
            )

    def _load_model_with_retry(self, n_retry: int, n_batch: int,
                                use_mlock: bool, use_mmap: bool) -> Llama:
        """Carga el modelo con reintentos automáticos."""
        last_error = None

        for attempt in range(1, n_retry + 1):
            try:
                logger.debug(f"Cargando modelo (intento {attempt}/{n_retry})...")
                return Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    n_gpu_layers=self.n_gpu_layers,
                    verbose=self.verbose,
                    n_batch=n_batch,
                    use_mlock=use_mlock,
                    use_mmap=use_mmap,
                )
            except Exception as e:
                last_error = e
                logger.warning(f"Intento {attempt} fallido: {e}")
                if attempt < n_retry:
                    time.sleep(1 * attempt)  # Backoff exponencial

        raise LlamaCppModelLoadError(
            f"Failed to load model after {n_retry} attempts: {last_error}"
        )

    def generate_response(self, prompt: str, max_tokens: int | None = None) -> str:
        """
        Genera una respuesta de texto basada en un prompt.

        Args:
            prompt: Prompt de entrada
            max_tokens: Máximo de tokens (override del constructor)

        Returns:
            Respuesta generada
        """
        tokens = self.generate_stream(prompt, max_tokens)
        return "".join(tokens)

    def generate_stream(self, prompt: str,
                        max_tokens: int | None = None) -> Generator[str, None, None]:
        """
        Genera una respuesta en streaming (token por token).

        Args:
            prompt: Prompt de entrada
            max_tokens: Máximo de tokens

        Yields:
            Tokens generados uno por uno
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        response = self.llm(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
            stop=self.stop_tokens,
            echo=False,
            stream=True,
        )

        for output in response:
            token = output["choices"][0]["text"]
            if token:
                yield token

    def get_model(self) -> Any:
        """Devuelve la instancia de Llama para integración con LangChain."""
        return self.llm

    def get_model_info(self) -> dict[str, Any]:
        """Obtiene información del modelo cargado."""
        return {
            "model_path": self.model_path,
            "n_ctx": self.n_ctx,
            "n_threads": self.n_threads,
            "n_gpu_layers": self.n_gpu_layers,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stop_tokens": self.stop_tokens,
            "model_size_mb": os.path.getsize(self.model_path) / (1024 * 1024),
        }

    def get_usage_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas de uso del modelo."""
        return {
            "context_used": self.llm.n_ctx if hasattr(self.llm, 'n_ctx') else 0,
            "batch_size": self.n_batch,
            "gpu_layers": self.n_gpu_layers,
        }
