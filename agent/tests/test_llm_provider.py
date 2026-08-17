"""Tests for provider registry, selection and the deterministic MockProvider."""

import pytest

from app.core.config import settings
from app.llm.client import (
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)
from app.llm.models import LLMNotConfigured, ProviderRequest
from app.llm.provider import (
    MockProvider,
    build_provider,
    is_configured,
    provider_default_model,
    provider_for_name,
    provider_requires_key,
    providers_info,
    resolve_provider,
)


def _request(**overrides):
    values = {
        "model": "mock-model",
        "system_prompt": "system",
        "user_prompt": (
            "# Role: analyze\n# EVIDENCE\n- evidence_id: code:src/app.py:10 | "
            "chunk_id: chunk:src/app.py:10 | file: src/app.py | lines: 10-20"
        ),
    }
    values.update(overrides)
    return ProviderRequest(**values)


def test_mock_provider_default_configuration():
    assert is_configured("mock", settings) is True


def test_mock_provider_never_needs_key():
    assert provider_default_model("mock") == "mock-model"
    assert provider_default_model("unknown-name") == "mock-model"


def test_resolve_provider_default_is_mock():
    name, configured = resolve_provider(settings)
    assert name == "mock"
    assert configured is True


def test_resolve_provider_falls_back_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openai")
    monkeypatch.setattr(settings, "agent_llm_api_key", "")
    monkeypatch.setattr(settings, "agent_openai_api_key", "")
    name, configured = resolve_provider(settings)
    assert name == "mock"
    assert configured is False


def test_resolve_provider_keeps_configured_openai(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openai")
    monkeypatch.setattr(settings, "agent_llm_api_key", "sk-test1234567890")
    name, configured = resolve_provider(settings)
    assert name == "openai"
    assert configured is True


def test_is_configured_ollama_always():
    assert is_configured("ollama", settings) is True


def test_is_configured_anthropic_uses_llm_or_dedicated_key(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_api_key", "")
    monkeypatch.setattr(settings, "agent_anthropic_api_key", "")
    assert is_configured("anthropic", settings) is False
    monkeypatch.setattr(settings, "agent_anthropic_api_key", "sk-ant-test")
    assert is_configured("anthropic", settings) is True


def test_build_provider_mock_returns_mock_instance():
    provider = build_provider(settings)
    assert isinstance(provider, MockProvider)


def test_provider_for_name_mock():
    provider = provider_for_name("mock", settings, timeout=10.0)
    assert isinstance(provider, MockProvider)


def test_provider_for_name_unconfigured_raises(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_api_key", "")
    monkeypatch.setattr(settings, "agent_openai_api_key", "")
    with pytest.raises(LLMNotConfigured):
        provider_for_name("openai", settings, timeout=10.0)


def test_providers_info_lists_all_five():
    info = providers_info(settings)
    names = {entry.name for entry in info}
    assert names == {"openai", "anthropic", "google", "ollama", "mock"}
    mock = next(entry for entry in info if entry.name == "mock")
    assert mock.deterministic is True
    assert mock.configured is True
    assert mock.default_model == "mock-model"


def test_mock_provider_complete_returns_grounded_json():
    provider = MockProvider(latency_ms=0)
    response = provider.complete(_request())
    assert response.content
    assert "evidence_id" in response.content
    assert "src/app.py" in response.content
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.finish_reason == "stop"
    assert response.retries == 0


def test_mock_provider_parses_evidence_lines():
    provider = MockProvider(latency_ms=0)
    user_prompt = (
        "# EVIDENCE\n"
        "- evidence_id: code:a.py:3 | chunk_id: chunk:a.py:3 | file: a.py | lines: 3-3\n"
        "- evidence_id: code:b.py:7 | chunk_id: chunk:b.py:7 | file: b.py | lines: 7-9"
    )
    response = provider.complete(_request(user_prompt=user_prompt))
    assert "a.py" in response.content
    assert "b.py" in response.content


def test_mock_provider_detects_explain_role():
    provider = MockProvider(latency_ms=0)
    response = provider.complete(_request(user_prompt="# Role: explain\n# EVIDENCE\n"))
    assert '"explanation"' in response.content


def test_provider_requires_key_flags_cloud_providers():
    assert provider_requires_key("openai") is True
    assert provider_requires_key("anthropic") is True
    assert provider_requires_key("google") is True
    assert provider_requires_key("ollama") is False
    assert provider_requires_key("mock") is False


def test_is_configured_google_uses_dedicated_key(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_api_key", "")
    monkeypatch.setattr(settings, "agent_google_api_key", "")
    assert is_configured("google", settings) is False
    monkeypatch.setattr(settings, "agent_google_api_key", "AIza-test")
    assert is_configured("google", settings) is True


def test_is_configured_unknown_name_is_false():
    assert is_configured("unknown-name", settings) is False


def test_build_provider_each_configured_provider(monkeypatch):
    cases = [
        ("openai", "sk-test", OpenAIProvider),
        ("anthropic", "sk-ant-test", AnthropicProvider),
        ("google", "AIza-test", GeminiProvider),
        ("ollama", None, OllamaProvider),
    ]
    for name, key, expected in cases:
        monkeypatch.setattr(settings, "agent_llm_provider", name)
        monkeypatch.setattr(settings, "agent_llm_api_key", key or "")
        monkeypatch.setattr(settings, "agent_openai_api_key", "")
        monkeypatch.setattr(settings, "agent_anthropic_api_key", "")
        monkeypatch.setattr(settings, "agent_google_api_key", "")
        provider = build_provider(settings)
        assert isinstance(provider, expected), name
        assert provider.name == name


def test_build_provider_falls_back_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openai")
    monkeypatch.setattr(settings, "agent_llm_api_key", "")
    monkeypatch.setattr(settings, "agent_openai_api_key", "")
    provider = build_provider(settings)
    assert isinstance(provider, MockProvider)
    assert provider.name == "mock"


def test_provider_for_name_each_configured_provider(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_api_key", "sk-test")
    cases = [
        ("openai", OpenAIProvider),
        ("anthropic", AnthropicProvider),
        ("google", GeminiProvider),
        ("ollama", OllamaProvider),
    ]
    for name, expected in cases:
        provider = provider_for_name(name, settings, timeout=10.0)
        assert isinstance(provider, expected), name
        assert provider.name == name
