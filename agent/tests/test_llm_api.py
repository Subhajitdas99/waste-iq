"""Tests for the /api/llm/* endpoints."""

from app.core.config import settings
from app.review.review_models import ReviewFinding


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


def _analyze_payload(**overrides):
    values = {
        "repository": "acme/app",
        "findings": [_finding().model_dump()],
        "rules_used": ["R1"],
    }
    values.update(overrides)
    return values


def test_analyze_endpoint_returns_grounded_analysis(client):
    response = client.post("/api/llm/analyze", json=_analyze_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]
    assert body["provider"] == "mock"
    assert body["cached"] is False
    assert body["references"][0]["file_path"] == "src/app.py"


def test_analyze_endpoint_propagates_request_id(client):
    response = client.post(
        "/api/llm/analyze", json=_analyze_payload(), headers={"x-request-id": "req-abc"}
    )
    assert response.status_code == 200
    assert response.json()["correlation_id"] == "req-abc"


def test_explain_endpoint_requires_question(client):
    response = client.post("/api/llm/explain", json={"repository": "acme/app"})
    assert response.status_code == 422


def test_explain_endpoint_success(client):
    response = client.post(
        "/api/llm/explain",
        json={"repository": "acme/app", "question": "why?", "findings": [_finding().model_dump()]},
    )
    assert response.status_code == 200
    assert response.json()["explanation"]


def test_summarize_endpoint_success(client):
    response = client.post("/api/llm/summarize", json=_analyze_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["overview"]
    assert body["key_points"]


def test_analyze_unknown_provider_rejected(client):
    response = client.post("/api/llm/analyze", json=_analyze_payload(provider="amazon"))
    assert response.status_code == 422


def test_analyze_unconfigured_provider_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "agent_llm_api_key", "")
    monkeypatch.setattr(settings, "agent_openai_api_key", "")
    response = client.post("/api/llm/analyze", json=_analyze_payload(provider="openai"))
    assert response.status_code == 503


def test_analyze_rejects_extra_fields(client):
    response = client.post("/api/llm/analyze", json=_analyze_payload(hacked="x"))
    assert response.status_code == 422


def test_providers_endpoint(client):
    response = client.get("/api/llm/providers")
    assert response.status_code == 200
    names = {entry["name"] for entry in response.json()}
    assert names == {"openai", "anthropic", "google", "ollama", "openrouter", "mock"}


def test_status_endpoint(client):
    response = client.get("/api/llm/status")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["provider"] == "mock"
    assert body["cache_backend"] == "memory"
    assert body["by_provider"] == []


def test_status_reflects_activity(client):
    client.post("/api/llm/analyze", json=_analyze_payload())
    body = client.get("/api/llm/status").json()
    assert body["total_calls"] == 1
    assert body["by_provider"][0]["provider"] == "mock"


def test_cached_second_call(client):
    first = client.post("/api/llm/analyze", json=_analyze_payload())
    second = client.post("/api/llm/analyze", json=_analyze_payload())
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
