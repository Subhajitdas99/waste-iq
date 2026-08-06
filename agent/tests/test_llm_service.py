"""Tests for the LLM service: orchestration, retries, cache, grounding gate."""

import json

import pytest

from app.core.config import settings
from app.llm.models import (
    AnalyzeRequest,
    ExplainRequest,
    GroundingViolationError,
    LLMNotConfigured,
    LLMProviderError,
    LLMRetryableError,
    LLMTimeoutError,
    MalformedResponseError,
    ProviderRequest,
    ProviderResponse,
    RateLimitedError,
    SummarizeRequest,
)
from app.llm.service import LLMService
from app.review.review_models import ReviewFinding


class _FakeProvider:
    name = "fake"

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        if not self._responses:
            raise AssertionError("no responses left for fake provider")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


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
    elif role == "summarize":
        payload = {
            "overview": "a summary",
            "key_points": ["kp"],
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


def _mock_response(content):
    return ProviderResponse(
        content=content, model="mock-model", prompt_tokens=10, completion_tokens=5
    )


def _service_with(provider, monkeypatch, **settings_overrides):
    monkeypatch.setattr(settings, "agent_llm_cache_enabled", False)
    monkeypatch.setattr(settings, "agent_llm_max_retries", 2)
    monkeypatch.setattr(settings, "agent_llm_retry_backoff_seconds", 0.0)
    monkeypatch.setattr(settings, "agent_llm_rate_limit_per_minute", 1000)
    for key, value in settings_overrides.items():
        monkeypatch.setattr(settings, key, value)
    return LLMService(settings=settings, provider=provider)


def test_analyze_with_mock_provider_returns_grounded_response(monkeypatch):
    service = LLMService(settings=settings)
    response = service.analyze(_analyze_request())
    assert response.provider == "mock"
    assert response.cached is False
    assert response.summary
    assert response.references
    assert response.references[0].file_path == "src/app.py"
    assert response.correlation_id is None


def test_analyze_propagates_correlation_id(monkeypatch):
    service = LLMService(settings=settings)
    response = service.analyze(_analyze_request(), correlation_id="req-1")
    assert response.correlation_id == "req-1"


def test_cache_hit_returns_cached_flag(monkeypatch):
    provider = _FakeProvider([_mock_response(_grounded_content())])
    monkeypatch.setattr(settings, "agent_llm_cache_enabled", True)
    monkeypatch.setattr(settings, "agent_llm_cache_backend", "memory")
    service = LLMService(settings=settings, provider=provider)
    first = service.analyze(_analyze_request())
    second = service.analyze(_analyze_request())
    assert first.cached is False
    assert second.cached is True
    assert provider.calls == 1
    status = service.status()
    assert status.cache_hits == 1
    assert status.cache_misses == 1


def test_grounding_violation_rejects_unsupported_file(monkeypatch):
    content = _grounded_content(path="ghost.py", start=1, end=2)
    provider = _FakeProvider([_mock_response(content)])
    service = _service_with(provider, monkeypatch)
    with pytest.raises(GroundingViolationError):
        service.analyze(_analyze_request())


def test_malformed_response_rejected(monkeypatch):
    provider = _FakeProvider([_mock_response("this is not json")])
    service = _service_with(provider, monkeypatch)
    with pytest.raises(MalformedResponseError):
        service.analyze(_analyze_request())


def test_disabled_layer_raises_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_enabled", False)
    service = LLMService(settings=settings)
    with pytest.raises(LLMNotConfigured):
        service.analyze(_analyze_request())


def test_retry_then_success_records_retries(monkeypatch):
    provider = _FakeProvider(
        [
            LLMRetryableError("temporarily unavailable"),
            _mock_response(_grounded_content()),
        ]
    )
    service = _service_with(provider, monkeypatch)
    response = service.analyze(_analyze_request())
    assert response.summary
    assert provider.calls == 2
    status = service.status()
    assert status.retries == 1
    aggregate = status.by_provider[0]
    assert aggregate.provider == "fake"
    assert aggregate.calls == 1
    assert aggregate.failures == 0


def test_retries_exhausted_raises_provider_error(monkeypatch):
    provider = _FakeProvider(
        [
            LLMRetryableError("unavailable"),
            LLMRetryableError("unavailable"),
            LLMRetryableError("unavailable"),
        ]
    )
    service = _service_with(provider, monkeypatch)
    with pytest.raises(LLMProviderError):
        service.analyze(_analyze_request())
    status = service.status()
    assert status.failed_calls == 1
    assert status.retries == 2


def test_rate_limit_blocks_second_call(monkeypatch):
    provider = _FakeProvider([_mock_response(_grounded_content())])
    service = _service_with(provider, monkeypatch, agent_llm_rate_limit_per_minute=1)
    service.analyze(_analyze_request(repository="acme/app"))
    with pytest.raises(RateLimitedError):
        service.analyze(_analyze_request(repository="acme/app"))


def test_explain_and_summarize_roles(monkeypatch):
    service = LLMService(settings=settings)
    explain = service.explain(
        ExplainRequest(repository="acme/app", question="why?", findings=[_finding()])
    )
    assert explain.explanation
    summary = service.summarize(SummarizeRequest(repository="acme/app", findings=[_finding()]))
    assert summary.overview
    assert summary.key_points


def test_provider_override_mock(monkeypatch):
    service = LLMService(settings=settings)
    response = service.analyze(_analyze_request(provider="mock"))
    assert response.provider == "mock"


def test_status_reflects_configuration(monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_provider", "openai")
    monkeypatch.setattr(settings, "agent_llm_api_key", "")
    monkeypatch.setattr(settings, "agent_openai_api_key", "")
    service = LLMService(settings=settings)
    status = service.status()
    assert status.enabled is True
    assert status.provider == "mock"
    assert status.configured is False
    assert status.deterministic_fallback is True
    assert status.cache_backend == settings.agent_llm_cache_backend


def test_status_empty_before_calls():
    service = LLMService(settings=settings)
    status = service.status()
    assert status.total_calls == 0
    assert status.by_provider == []


def test_telemetry_aggregates_cost_and_tokens(monkeypatch):
    service = LLMService(settings=settings)
    service.analyze(_analyze_request())
    status = service.status()
    assert status.total_calls == 1
    assert status.total_prompt_tokens > 0
    assert status.total_completion_tokens > 0
    assert status.estimated_cost >= 0
    assert status.average_latency_ms >= 0


def test_providers_list():
    service = LLMService(settings=settings)
    names = {entry.name for entry in service.providers()}
    assert names == {"openai", "anthropic", "google", "ollama", "mock"}


def test_rate_limiter_purges_old_window_and_resets():
    import time as _time

    from app.llm.service import RateLimiter

    limiter = RateLimiter(max_per_minute=2)
    limiter._window.append(_time.monotonic() - 61.0)  # noqa: SLF001
    assert limiter.allow() is True
    limiter.reset()
    assert len(limiter._window) == 0
    full = RateLimiter(max_per_minute=1)
    assert full.allow() is True
    assert full.allow() is False


def test_empty_provider_content_is_malformed(monkeypatch):
    provider = _FakeProvider([ProviderResponse(content="")])
    service = _service_with(provider, monkeypatch)
    with pytest.raises(MalformedResponseError):
        service.analyze(_analyze_request())


def test_timeout_error_propagates(monkeypatch):
    provider = _FakeProvider([LLMTimeoutError("too slow")])
    service = _service_with(provider, monkeypatch)
    with pytest.raises(LLMTimeoutError):
        service.analyze(_analyze_request())
    assert service.status().failed_calls == 1


def test_non_retryable_error_propagates(monkeypatch):
    provider = _FakeProvider([MalformedResponseError("bad output")])
    service = _service_with(provider, monkeypatch)
    with pytest.raises(MalformedResponseError):
        service.analyze(_analyze_request())
    assert service.status().failed_calls == 1
