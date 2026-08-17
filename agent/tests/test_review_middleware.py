"""Tests for the request-correlation middleware."""


def test_response_always_has_request_id(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"]


def test_inbound_request_id_is_echoed(client):
    response = client.get("/api/health", headers={"x-request-id": "custom-123"})
    assert response.headers["x-request-id"] == "custom-123"


def test_api_review_uses_correlation_header(client):
    response = client.get("/api/review/status", headers={"x-request-id": "corr-api-1"})
    assert response.headers["x-request-id"] == "corr-api-1"
