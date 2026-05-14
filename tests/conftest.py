import pytest
import os

os.environ.setdefault("MINIMAX_API_KEY", "sk-test-minimax-key")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-openai-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-anthropic-key")


@pytest.fixture
def cloud_llm_minimax():
    from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
    return CloudLLMAdapter(provider="minimax")


@pytest.fixture
def cloud_llm_openai():
    from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
    return CloudLLMAdapter(provider="openai")


@pytest.fixture
def cloud_llm_anthropic():
    from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
    return CloudLLMAdapter(provider="anthropic")


@pytest.fixture
def cloud_llm_google():
    from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
    return CloudLLMAdapter(provider="google")


@pytest.fixture
def cloud_llm_groq():
    from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
    return CloudLLMAdapter(provider="groq")


@pytest.fixture
def cloud_llm_deepseek():
    from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
    return CloudLLMAdapter(provider="deepseek")