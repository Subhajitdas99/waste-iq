"""API tests for the Developer Chat Assistant endpoints (Phase 5)."""

import pytest

from app.chat.models import ChatNotFoundError, ChatValidationError


@pytest.fixture
def indexed_container(client, clean_context_db):
    from app.api.dependencies import get_container

    container = get_container()
    container.pipeline().run()
    yield container


def test_chat_returns_grounded_answer(client, indexed_container):
    response = client.post(
        "/api/chat",
        json={"question": "Where is the Calculator?"},
        headers={"X-Request-ID": "req-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "find_implementation"
    assert body["grounded"] is True
    assert body["references"]
    assert body["conversation_id"]
    assert body["correlation_id"] == "req-1"
    assert body["provider"] == "mock"
    assert body["latency_ms"] >= 0
    assert any("src/utils.py" in ref["file_path"] for ref in body["references"])


def test_chat_unknown_question_returns_help(client, indexed_container):
    response = client.post("/api/chat", json={"question": "hello there"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "unknown"
    assert body["grounded"] is False
    assert body["references"] == []
    assert "Try:" in body["answer"]


def test_chat_followup_uses_same_conversation(client, indexed_container):
    first = client.post("/api/chat", json={"question": "Where is the Calculator?"}).json()
    second = client.post(
        "/api/chat/followup",
        json={"question": "what about it?", "conversation_id": first["conversation_id"]},
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == first["conversation_id"]


def test_chat_followup_unknown_conversation_404(client, indexed_container):
    response = client.post(
        "/api/chat/followup", json={"question": "what about it?", "conversation_id": "missing"}
    )
    assert response.status_code == 404


def test_chat_rejects_secret_shaped_question(client, indexed_container):
    response = client.post(
        "/api/chat",
        json={"question": "What is the api_key=sk-abcdefghijklmnopqrstuvwxyz123456?"},
    )
    assert response.status_code == 422


def test_chat_rejects_empty_question(client):
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 422


def test_chat_rejects_oversized_question(client, indexed_container):
    response = client.post("/api/chat", json={"question": "x" * 5000})
    assert response.status_code == 422


def test_chat_no_evidence_rejected(client, clean_context_db):
    response = client.post(
        "/api/chat", json={"question": "Generate an issue draft for the login failure"}
    )
    assert response.status_code == 422


def test_chat_status_endpoint(client):
    response = client.get("/api/chat/status")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["provider"] == "mock"
    assert body["cache_backend"] == "memory"
    assert body["max_turns"] == 10
    assert "intent_counts" in body


def test_chat_status_tracks_intent_counts(client, indexed_container):
    client.post("/api/chat", json={"question": "Where is the Calculator?"})
    status = client.get("/api/chat/status").json()
    assert status["intent_counts"]["find_implementation"] == 1
    assert status["memory_turns"] == 1


def test_consider_maps_upstream_errors():
    from fastapi import HTTPException

    from app.chat.router import _consider
    from app.llm.models import LLMProviderError, LLMTimeoutError, RateLimitedError
    from app.review.review_models import ReviewUnavailable

    assert _consider(ChatValidationError("bad")).status_code == 422
    assert _consider(ChatNotFoundError("nope")).status_code == 404
    assert _consider(ReviewUnavailable("nope")).status_code == 422
    assert _consider(LLMTimeoutError("slow")).status_code == 504
    assert _consider(RateLimitedError("slow down")).status_code == 429
    assert _consider(LLMProviderError("boom")).status_code == 502
    assert _consider(RuntimeError("other")).status_code == 502
    assert isinstance(_consider(RuntimeError("x")), HTTPException)
