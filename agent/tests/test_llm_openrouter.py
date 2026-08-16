"""Tests for the OpenRouter provider (Phase 5.1).

Covers: provider selection, client HTTP behavior (headers, body, parsing),
configuration, error handling, timeout, retry policy, telemetry, cache
integration, redaction and grounding — all with mocked HTTP transport, no
internet calls.
"""

import json
import re

import httpx
import pytest
import respx

from app.core.config import Settings, settings
from app.llm.cache import hash_request
from app.llm.models import (
    AnalyzeRequest,
    ExplainRequest,
    GroundingViolationError,
    LLMNotConfigured,
    LLMProviderError,
    LLMRetryableError,
    LLMTimeoutError,
    ProviderRequest,
)
from app.llm.provider import (
    MockProvider,
    build_provider,
    is_configured,
    provider_base_url,
    provider_default_model,
    provider_for_name,
    providers_info,
    resolve_provider,
)
from app.llm.providers.openrouter import OpenRouterProvider
from app.llm.service import LLMService
from app.review.review_models import ReviewFinding

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = "sk-or-test-0123456789abcdef"


def _request(**overrides):
    values = {
        "model": "openai/gpt-4o-mini",
        "system_prompt": "system",
        "user_prompt": "user",
        "max_tokens": 500,
        "temperature": 0.0,
        "timeout": 5.0,
    }
    values.update(overrides)
    return ProviderRequest(**values)


def _provider(**overrides):
    values = {"api_key": API_KEY, "base_url": "https://openrouter.ai/api/v1", "model": "m"}
    values.update(overrides)
    return OpenRouterProvider(**values)


def _openai_style_body(content='"ok"', prompt_tokens=12, completion_tokens=4):
    return {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        "model": "openai/gpt-4o-mini",
    }


def _finding(path="src/app.py", start=10, end=20):
    return ReviewFinding(
        rule_id="R1",
        category="security",
        severity="high",
        title="title",
        explanation="explanation",
        file_path=path,
        start_line=start,
        end_line=end,
        snippet="password = 'hunter2-secret'",
    )


def _analyze_request(**overrides):
    values = {
        "repository": "acme/app",
        "findings": [_finding()],
        "rules_used": ["R1"],
    }
    values.update(overrides)
    return AnalyzeRequest(**values)


def _grounded_content(role="analyze", path="src/app.py", start=10, end=20):
    ref = {
        "file_path": path,
        "start_line": start,
        "end_line": end,
        "evidence_id": f"code:{path}:{start}",
        "chunk_id": f"chunk:{path}:{start}",
    }
    if role == "explain":
        payload = {
            "explanation": "because the code says so",
            "confidence": 0.8,
            "references": [ref],
        }
    else:
        payload = {
            "summary": "an analysis",
            "priorities": ["p"],
            "recommendations": ["r"],
            "risks": ["risk"],
            "confidence": 0.8,
            "references": [ref],
        }
    return json.dumps(payload)


def _service_with(provider, monkeypatch, **settings_overrides):
    monkeypatch.setattr(settings, "agent_llm_cache_enabled", False)
    monkeypatch.setattr(settings, "agent_llm_max_retries", 2)
    monkeypatch.setattr(settings, "agent_llm_retry_backoff_seconds", 0.0)
    monkeypatch.setattr(settings, "agent_llm_rate_limit_per_minute", 1000)
    for key, value in settings_overrides.items():
        monkeypatch.setattr(settings, key, value)
    return LLMService(settings=settings, provider=provider)


# ---------------------------------------------------------------------------
# Configuration


def test_default_base_url():
    assert provider_base_url("openrouter") == "https://openrouter.ai/api/v1"


def test_default_model():
    assert provider_default_model("openrouter") == "openai/gpt-4o-mini"


def test_is_configured_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "agent_openrouter_api_key", "")
    assert is_configured("openrouter", settings) is False
    monkeypatch.setattr(settings, "agent_openrouter_api_key", API_KEY)
    assert is_configured("openrouter", settings) is True


def test_settings_env_aliases():
    parsed = Settings(
        agent_openrouter_api_key=API_KEY,
        agent_openrouter_base_url="https://proxy.example/v1",
        agent_openrouter_http_referer="https://waste-iq.dev",
        agent_openrouter_app_name="Waste-IQ Agent",
    )
    assert parsed.agent_openrouter_api_key == API_KEY
    assert parsed.agent_openrouter_base_url == "https://proxy.example/v1"
    assert parsed.agent_openrouter_http_referer == "https://waste-iq.dev"
    assert parsed.agent_openrouter_app_name == "Waste-IQ Agent"
    default = Settings(agent_openrouter_api_key="")
    assert default.agent_openrouter_base_url == "https://openrouter.ai/api/v1"


def test_unknown_provider_configuration_error(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "bogus")
    with pytest.raises(LLMNotConfigured, match=r"unknown LLM provider 'bogus'"):
        resolve_provider(settings)


def test_provider_for_name_unknown_raises_clear_error():
    with pytest.raises(LLMNotConfigured, match=r"unknown provider 'bogus'"):
        provider_for_name("bogus", settings, timeout=10.0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Provider selection


def test_resolve_provider_openrouter_configured(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openrouter")
    monkeypatch.setattr(settings, "agent_openrouter_api_key", API_KEY)
    name, configured = resolve_provider(settings)
    assert (name, configured) == ("openrouter", True)


def test_resolve_provider_openrouter_unconfigured_falls_back(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openrouter")
    monkeypatch.setattr(settings, "agent_openrouter_api_key", "")
    name, configured = resolve_provider(settings)
    assert (name, configured) == ("mock", False)


def test_build_provider_returns_openrouter_instance(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openrouter")
    monkeypatch.setattr(settings, "agent_openrouter_api_key", API_KEY)
    monkeypatch.setattr(settings, "agent_openrouter_http_referer", "https://waste-iq.dev")
    monkeypatch.setattr(settings, "agent_openrouter_app_name", "Waste-IQ Agent")
    provider = build_provider(settings)
    assert isinstance(provider, OpenRouterProvider)
    assert provider.name == "openrouter"
    assert provider._api_key == API_KEY  # noqa: SLF001
    assert provider._http_referer == "https://waste-iq.dev"  # noqa: SLF001
    assert provider._app_name == "Waste-IQ Agent"  # noqa: SLF001


def test_build_provider_openrouter_unconfigured_returns_mock(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openrouter")
    monkeypatch.setattr(settings, "agent_openrouter_api_key", "")
    provider = build_provider(settings)
    assert isinstance(provider, MockProvider)


def test_provider_for_name_openrouter(monkeypatch):
    monkeypatch.setattr(settings, "agent_openrouter_api_key", API_KEY)
    provider = provider_for_name("openrouter", settings, timeout=10.0)
    assert isinstance(provider, OpenRouterProvider)


def test_provider_for_name_openrouter_unconfigured_raises(monkeypatch):
    monkeypatch.setattr(settings, "agent_openrouter_api_key", "")
    with pytest.raises(LLMNotConfigured):
        provider_for_name("openrouter", settings, timeout=10.0)


def test_providers_info_includes_openrouter(monkeypatch):
    monkeypatch.setattr(settings, "agent_openrouter_api_key", API_KEY)
    info = {entry.name: entry for entry in providers_info(settings)}
    openrouter = info["openrouter"]
    assert openrouter.configured is True
    assert openrouter.deterministic is False
    assert openrouter.default_model == "openai/gpt-4o-mini"
    assert openrouter.base_url == "https://openrouter.ai/api/v1"


# ---------------------------------------------------------------------------
# Client: request serialization and headers


@respx.mock
def test_openrouter_success_headers_and_body():
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(200, json=_openai_style_body()))
    provider = _provider()
    response = provider.complete(_request())
    assert response.content == '"ok"'
    assert response.prompt_tokens == 12
    assert response.completion_tokens == 4
    assert response.finish_reason == "stop"
    assert response.model == "openai/gpt-4o-mini"

    request = respx.calls.last.request
    assert str(request.url).startswith("https://openrouter.ai/api/v1/chat/completions")
    assert request.headers["authorization"] == f"Bearer {API_KEY}"
    assert request.headers["content-type"] == "application/json"
    assert "http-referer" not in request.headers
    assert "x-title" not in request.headers

    body = json.loads(request.content)
    assert body["model"] == "openai/gpt-4o-mini"
    assert body["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"},
    ]
    assert body["max_tokens"] == 500
    assert body["temperature"] == 0.0


@respx.mock
def test_openrouter_sends_optional_identity_headers():
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(200, json=_openai_style_body()))
    provider = _provider(http_referer="https://waste-iq.dev", app_name="Waste-IQ Agent")
    provider.complete(_request())
    request = respx.calls.last.request
    assert request.headers["http-referer"] == "https://waste-iq.dev"
    assert request.headers["x-title"] == "Waste-IQ Agent"


@respx.mock
def test_openrouter_custom_base_url():
    url = "https://proxy.example/v1/chat/completions"
    respx.post(url).mock(return_value=httpx.Response(200, json=_openai_style_body()))
    provider = _provider(base_url="https://proxy.example/v1")
    response = provider.complete(_request())
    assert response.content == '"ok"'
    assert str(respx.calls.last.request.url) == url


@respx.mock
def test_openrouter_usage_fallback_estimates_tokens():
    body = {
        "choices": [{"message": {"content": "short"}, "finish_reason": "stop"}],
        "model": "openai/gpt-4o-mini",
    }
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(200, json=body))
    response = _provider().complete(_request())
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0


# ---------------------------------------------------------------------------
# Client: error handling


@respx.mock
def test_openrouter_retryable_on_429():
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(429, json={}))
    with pytest.raises(LLMRetryableError):
        _provider().complete(_request())


@respx.mock
def test_openrouter_retryable_on_5xx():
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(503, json={}))
    with pytest.raises(LLMRetryableError):
        _provider().complete(_request())


@respx.mock
def test_openrouter_non_retryable_on_400():
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(400, json={"error": "invalid request"})
    )
    with pytest.raises(LLMProviderError):
        _provider().complete(_request())


@respx.mock
def test_openrouter_error_never_leaks_api_key_or_headers():
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(401, json={"error": "invalid api key"})
    )
    with pytest.raises(LLMProviderError) as excinfo:
        _provider().complete(_request())
    message = str(excinfo.value)
    assert API_KEY not in message
    assert "Bearer" not in message
    assert "Authorization" not in message


@respx.mock
def test_openrouter_timeout_raises_timeout_error():
    def _slow(request):
        raise httpx.ReadTimeout("timeout")

    respx.post(OPENROUTER_URL).mock(side_effect=_slow)
    with pytest.raises(LLMTimeoutError):
        _provider().complete(_request())


@respx.mock
def test_openrouter_network_error_is_retryable():
    def _network_error(request):
        raise httpx.ConnectError("connection refused")

    respx.post(OPENROUTER_URL).mock(side_effect=_network_error)
    with pytest.raises(LLMRetryableError):
        _provider().complete(_request())


# ---------------------------------------------------------------------------
# Service integration: retries, telemetry, cache, grounding, redaction


@respx.mock
def test_service_grounded_answer_uses_openrouter(monkeypatch):
    def _handler(request):
        return httpx.Response(200, json=_openai_style_body(_grounded_content()))

    respx.post(OPENROUTER_URL).mock(side_effect=_handler)
    service = _service_with(_provider(), monkeypatch)
    response = service.analyze(_analyze_request())
    assert response.provider == "openrouter"
    assert response.cached is False
    assert response.references
    body = json.loads(respx.calls.last.request.content)
    assert body["model"] == "openai/gpt-4o-mini"


@respx.mock
def test_service_retries_then_succeeds(monkeypatch):
    responses = [
        httpx.Response(503, json={}),
        httpx.Response(200, json=_openai_style_body(_grounded_content())),
    ]
    respx.post(OPENROUTER_URL).mock(side_effect=responses)
    service = _service_with(_provider(), monkeypatch)
    response = service.analyze(_analyze_request())
    assert response.provider == "openrouter"
    status = service.status()
    aggregate = next(a for a in status.by_provider if a.provider == "openrouter")
    assert aggregate.calls == 1
    assert aggregate.retries == 1


@respx.mock
def test_service_retries_exhausted_raises(monkeypatch):
    respx.post(OPENROUTER_URL).mock(return_value=httpx.Response(503, json={}))
    service = _service_with(_provider(), monkeypatch)
    with pytest.raises(LLMProviderError):
        service.analyze(_analyze_request())
    status = service.status()
    aggregate = next(a for a in status.by_provider if a.provider == "openrouter")
    assert aggregate.failures == 1
    assert aggregate.calls == 1


@respx.mock
def test_service_timeout_propagates(monkeypatch):
    def _slow(request):
        raise httpx.ReadTimeout("timeout")

    respx.post(OPENROUTER_URL).mock(side_effect=_slow)
    service = _service_with(_provider(), monkeypatch)
    with pytest.raises(LLMTimeoutError):
        service.analyze(_analyze_request())


@respx.mock
def test_service_telemetry_tracks_openrouter_separately(monkeypatch):
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(
            200,
            json=_openai_style_body(_grounded_content(), prompt_tokens=100, completion_tokens=50),
        )
    )
    service = _service_with(
        _provider(),
        monkeypatch,
        agent_llm_provider="openrouter",
        agent_openrouter_api_key=API_KEY,
    )
    service.analyze(_analyze_request())
    status = service.status()
    assert status.provider == "openrouter"
    assert status.model == "openai/gpt-4o-mini"
    assert status.total_calls == 1
    assert status.total_prompt_tokens == 100
    assert status.total_completion_tokens == 50
    assert status.estimated_cost > 0
    aggregate = next(a for a in status.by_provider if a.provider == "openrouter")
    assert aggregate.total_prompt_tokens == 100
    assert aggregate.total_completion_tokens == 50
    assert aggregate.average_latency_ms >= 0
    assert aggregate.estimated_cost > 0


@respx.mock
def test_service_cache_hit_counts_and_skips_provider(monkeypatch):
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=_openai_style_body(_grounded_content()))
    )
    service = _service_with(
        _provider(),
        monkeypatch,
        agent_llm_cache_enabled=True,
        agent_llm_cache_backend="memory",
    )
    first = service.analyze(_analyze_request())
    second = service.analyze(_analyze_request())
    assert first.cached is False
    assert second.cached is True
    assert len(respx.calls) == 1
    status = service.status()
    assert status.cache_hits == 1
    assert status.cache_misses == 1
    aggregate = next(a for a in status.by_provider if a.provider == "openrouter")
    assert aggregate.calls == 1


def test_cache_key_includes_provider_and_model():
    base = hash_request("openrouter", "openai/gpt-4o-mini", "system", "user")
    other_provider = hash_request("openai", "openai/gpt-4o-mini", "system", "user")
    other_model = hash_request("openrouter", "anthropic/claude-3.5-haiku", "system", "user")
    other_prompt = hash_request("openrouter", "openai/gpt-4o-mini", "system", "user2")
    assert base != other_provider
    assert base != other_model
    assert base != other_prompt


@respx.mock
def test_secrets_redacted_before_reaching_openrouter(monkeypatch):
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=_openai_style_body(_grounded_content()))
    )
    service = _service_with(_provider(), monkeypatch)
    response = service.analyze(_analyze_request())
    assert response.provider == "openrouter"
    sent = json.loads(respx.calls.last.request.content)
    user_prompt = sent["messages"][1]["content"]
    assert "hunter2-secret" not in user_prompt
    assert "[REDACTED]" in user_prompt
    assert API_KEY not in json.dumps(sent)


@respx.mock
def test_grounding_rejection_still_works(monkeypatch):
    ungrounded = json.dumps({"summary": "made up", "confidence": 0.9, "references": []})
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=_openai_style_body(ungrounded))
    )
    service = _service_with(_provider(), monkeypatch)
    with pytest.raises(GroundingViolationError):
        service.analyze(_analyze_request())


@respx.mock
def test_explain_role_with_openrouter(monkeypatch):
    respx.post(OPENROUTER_URL).mock(
        return_value=httpx.Response(200, json=_openai_style_body(_grounded_content("explain")))
    )
    service = _service_with(_provider(), monkeypatch)
    response = service.explain(
        ExplainRequest(
            repository="acme/app",
            question="explain it",
            findings=[_finding()],
        )
    )
    assert response.provider == "openrouter"
    assert response.explanation
    assert response.references


# ---------------------------------------------------------------------------
# Chat API verification with the OpenRouter provider (mock transport)


_EVIDENCE_LINE_RE = (
    r"\bevidence_id:\s*([^\s|]+).*?\bfile:\s*([^\s|]+).*?\blines:\s*(\d+)(?:-(\d+))?"
)


def _evidence_echo_response(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    user_prompt = body["messages"][1]["content"]
    evidence = re.findall(_EVIDENCE_LINE_RE, user_prompt)
    references = [
        {
            "file_path": path,
            "start_line": int(start),
            "end_line": int(end if end else start),
            "evidence_id": eid,
            "chunk_id": f"chunk:{path}:{start}",
        }
        for eid, path, start, end in evidence[:3]
    ]
    payload = {
        "explanation": "Deterministic OpenRouter-backed answer grounded in evidence.",
        "confidence": 0.7,
        "references": references,
    }
    return httpx.Response(
        200,
        json=_openai_style_body(json.dumps(payload), prompt_tokens=64, completion_tokens=32),
    )


@pytest.fixture
def chat_container(client, clean_context_db):
    from app.api.dependencies import get_container

    container = get_container()
    container.pipeline().run()
    yield container


@respx.mock
def test_chat_api_returns_grounded_answer_via_openrouter(client, chat_container, monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openrouter")
    monkeypatch.setattr(settings, "agent_openrouter_api_key", API_KEY)
    respx.post(OPENROUTER_URL).mock(side_effect=_evidence_echo_response)

    response = client.post("/api/chat", json={"question": "Where is the Calculator?"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "find_implementation"
    assert body["provider"] == "openrouter"
    assert body["grounded"] is True
    assert body["references"]
    assert any("src/utils.py" in ref["file_path"] for ref in body["references"])
    assert "OpenRouter-backed answer" in body["answer"]

    status = client.get("/api/llm/status").json()
    assert status["provider"] == "openrouter"
    assert status["configured"] is True
    aggregate = next(a for a in status["by_provider"] if a["provider"] == "openrouter")
    assert aggregate["calls"] == 1
    assert aggregate["total_prompt_tokens"] == 64


@respx.mock
def test_chat_api_rejects_hallucinated_answer_via_openrouter(client, chat_container, monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openrouter")
    monkeypatch.setattr(settings, "agent_openrouter_api_key", API_KEY)

    def _ungrounded(request):
        payload = {
            "explanation": "Everything is made up.",
            "confidence": 0.9,
            "references": [{"file_path": "made/up.py", "start_line": 1, "end_line": 2}],
        }
        return httpx.Response(200, json=_openai_style_body(json.dumps(payload)))

    respx.post(OPENROUTER_URL).mock(side_effect=_ungrounded)
    response = client.post("/api/chat", json={"question": "Where is the Calculator?"})
    assert response.status_code == 422
    assert "rejected" in response.json()["detail"].lower()
