"""
Adapter factory for local and cloud LLM adapters.

Provides unified interface to get the appropriate adapter based on mode.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.ports.llm_port import LLMPort


def get_llm_adapter(
    mode: str,
    provider: str = "minimax",
    model: str | None = None,
    api_key: str | None = None,
) -> "LLMPort":
    """
    Factory function to get the appropriate LLM adapter.

    Args:
        mode: "local" or "cloud"
        provider: Cloud provider name (for cloud mode)
        model: Model name (optional, uses default if not specified)
        api_key: API key for cloud providers (optional, uses env var)

    Returns:
        LLM adapter instance (CloudLLMAdapter or LlamaCppLLMAdapter)

    Raises:
        RuntimeError: If required configuration is missing
    """

    if mode == "local":
        return _get_local_adapter()
    return _get_cloud_adapter(provider, model, api_key)


def _get_local_adapter() -> "LLMPort":
    """Get local llama.cpp adapter."""
    import os
    from pathlib import Path

    from src.infrastructure.adapters.llama_cpp_llm_adapter import LlamaCppLLMAdapter

    model_path = os.environ.get(
        "LLAMA_CPP_MODEL_PATH", "./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf"
    )
    model_path = str(Path(model_path).expanduser().resolve())

    if not Path(model_path).exists():
        raise RuntimeError(
            f"Local model not found: {model_path}\n"
            f"Set LLAMA_CPP_MODEL_PATH in .env or download a GGUF model"
        )

    adapter = LlamaCppLLMAdapter(
        model_path=model_path,
        n_ctx=4096,
        n_gpu_layers=0,
        temperature=0.1,
        max_tokens=2048,
        verbose=False,
    )

    return adapter


def _get_cloud_adapter(
    provider: str,
    model: str | None = None,
    api_key: str | None = None,
) -> "LLMPort":
    """Get cloud LLM adapter."""
    from pathlib import Path

    from dotenv import load_dotenv

    # Load .env if not already loaded
    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter

    return CloudLLMAdapter(
        provider=provider,
        model=model,
        api_key=api_key,
    )


def get_available_local_models() -> list[str]:
    """
    Get list of available local GGUF models in ./models directory.

    Returns:
        List of model filenames
    """
    from pathlib import Path

    models_dir = Path(__file__).parent.parent.parent.parent.parent / "models"

    if not models_dir.exists():
        return []

    return [f.name for f in models_dir.glob("*.gguf")]


def get_default_local_model() -> str | None:
    """
    Get the default local model path from environment.

    Returns:
        Model path or None if not set
    """
    import os
    from pathlib import Path

    model_path = os.environ.get("LLAMA_CPP_MODEL_PATH")

    if model_path:
        model_path = str(Path(model_path).expanduser().resolve())
        if Path(model_path).exists():
            return model_path

    # Try default location
    default_path = Path(__file__).parent.parent.parent.parent.parent / "models"
    gguf_files = list(default_path.glob("*.gguf"))

    if gguf_files:
        return str(gguf_files[0])

    return None
