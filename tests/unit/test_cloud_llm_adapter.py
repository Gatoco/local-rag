import pytest
from src.infrastructure.adapters.cloud_llm_adapter import (
    CloudLLMAdapter,
    CloudLLMConfigurationError,
    PROVIDER_CONFIG,
)


class TestCloudLLMAdapter:
    def test_provider_config_has_all_providers(self):
        expected = ["openai", "anthropic", "google", "groq", "minimax", "deepseek"]
        assert all(p in PROVIDER_CONFIG for p in expected)

    def test_minimax_has_correct_config(self):
        config = PROVIDER_CONFIG["minimax"]
        assert config["api_key_env"] == "MINIMAX_API_KEY"
        assert "MiniMax-M2.7-8k" in config["models"]
        assert config["default_model"] == "MiniMax-M2.7-8k"

    def test_openai_has_correct_config(self):
        config = PROVIDER_CONFIG["openai"]
        assert config["api_key_env"] == "OPENAI_API_KEY"
        assert "gpt-4o" in config["models"]
        assert config["default_model"] == "gpt-4o-mini"

    def test_adapter_stores_provider_and_model(self, cloud_llm_minimax):
        assert cloud_llm_minimax.provider == "minimax"
        assert cloud_llm_minimax.model == "MiniMax-M2.7-8k"

    def test_adapter_stores_custom_api_key(self):
        adapter = CloudLLMAdapter(provider="openai", api_key="sk-custom-key")
        assert adapter.api_key == "sk-custom-key"

    def test_adapter_uses_env_key_when_no_custom(self, cloud_llm_openai):
        assert cloud_llm_openai.api_key == "sk-test-openai-key"

    def test_get_available_providers(self):
        providers = CloudLLMAdapter.get_available_providers()
        assert len(providers) == 6
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
        assert "groq" in providers
        assert "minimax" in providers
        assert "deepseek" in providers

    def test_get_provider_models(self):
        models = CloudLLMAdapter.get_provider_models("openai")
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models

    def test_get_default_model(self):
        default = CloudLLMAdapter.get_default_model("minimax")
        assert default == "MiniMax-M2.7-8k"

    def test_invalid_provider_raises_error(self):
        with pytest.raises(CloudLLMConfigurationError):
            CloudLLMAdapter(provider="invalid_provider")

    def test_missing_api_key_raises_error(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(CloudLLMConfigurationError):
            CloudLLMAdapter(provider="openai", api_key=None)

    def test_get_model_info(self, cloud_llm_minimax):
        info = cloud_llm_minimax.get_model_info()
        assert info["provider"] == "minimax"
        assert info["model"] == "MiniMax-M2.7-8k"
        assert info["api_key_set"] is True
        assert "timeout" in info

    def test_model_case_insensitive(self):
        adapter = CloudLLMAdapter(provider="OPENAI", model="GPT-4O")
        assert adapter.provider == "openai"

    def test_custom_model_overrides_default(self):
        adapter = CloudLLMAdapter(provider="openai", model="gpt-4o")
        assert adapter.model == "gpt-4o"
        assert adapter.base_url == PROVIDER_CONFIG["openai"]["base_url"]

    def test_anthropic_has_correct_base_url(self):
        adapter = CloudLLMAdapter(provider="anthropic", api_key="sk-test")
        assert adapter.base_url == "https://api.anthropic.com/v1"

    def test_google_has_correct_base_url(self):
        adapter = CloudLLMAdapter(provider="google", api_key="sk-test")
        assert adapter.base_url == "https://generativelanguage.googleapis.com/v1beta"

    def test_groq_has_correct_base_url(self):
        adapter = CloudLLMAdapter(provider="groq", api_key="sk-test")
        assert adapter.base_url == "https://api.groq.com/openai/v1"

    def test_deepseek_has_correct_base_url(self):
        adapter = CloudLLMAdapter(provider="deepseek", api_key="sk-test")
        assert adapter.base_url == "https://api.deepseek.com/v1"

    def test_get_model_returns_self(self, cloud_llm_minimax):
        assert cloud_llm_minimax.get_model() is cloud_llm_minimax

    def test_unknown_provider_returns_empty_models(self):
        models = CloudLLMAdapter.get_provider_models("unknown")
        assert models == []

    def test_unknown_provider_returns_none_for_default(self):
        default = CloudLLMAdapter.get_default_model("unknown")
        assert default is None

    def test_all_providers_support_streaming(self):
        for provider, config in PROVIDER_CONFIG.items():
            assert config.get("supports_streaming") is True, f"{provider} should support streaming"

    def test_all_providers_have_models_list(self):
        for provider, config in PROVIDER_CONFIG.items():
            assert isinstance(config["models"], list)
            assert len(config["models"]) > 0

    def test_all_providers_have_default_model(self):
        for provider, config in PROVIDER_CONFIG.items():
            assert config["default_model"] in config["models"]