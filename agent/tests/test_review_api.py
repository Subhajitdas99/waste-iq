"""Tests for the PR review HTTP API."""

from app.review.review_models import ReviewRequest


def test_review_pr_endpoint(client, clean_review_db):
    response = client.post(
        "/api/review/pr",
        json=ReviewRequest(repository="waste-iq/demo", pr_number=1).model_dump(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["repo_full_name"] == "waste-iq/demo"
    assert data["pr_number"] == 1
    assert data["summary"]["total"] == len(data["findings"]) > 0
    assert data["findings"][0]["rule_id"]
    assert data["findings"][0]["evidence"] is not None
    assert data["disclaimers"]
    assert "x-request-id" in response.headers


def test_review_pr_endpoint_unknown_pr(client, clean_review_db):
    response = client.post(
        "/api/review/pr",
        json=ReviewRequest(repository="waste-iq/demo", pr_number=999).model_dump(),
    )
    assert response.status_code == 422
    assert "not found" in response.json()["detail"]


def test_review_status_endpoint(client, clean_review_db):
    response = client.get("/api/review/status")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True
    assert data["enabled"] is True
    assert data["engine_version"] == "2.0.0"
    assert data["total_sessions"] >= 0


def test_review_sessions_endpoint(client, clean_review_db):
    client.post(
        "/api/review/pr",
        json=ReviewRequest(repository="waste-iq/demo", pr_number=1).model_dump(),
    )
    response = client.get("/api/review/sessions?limit=5")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["status"] == "completed"


def test_review_session_detail_endpoint(client, clean_review_db):
    review = client.post(
        "/api/review/pr",
        json=ReviewRequest(repository="waste-iq/demo", pr_number=1).model_dump(),
    ).json()
    session_id = review["session_id"]

    response = client.get(f"/api/review/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["findings_count"] > 0
    assert data["metrics"]
    assert data["status"] == "completed"


def test_review_session_not_found(client, clean_review_db):
    response = client.get("/api/review/sessions/999999")
    assert response.status_code == 404


def test_review_session_invalid_limit(client):
    response = client.get("/api/review/sessions?limit=0")
    assert response.status_code == 422


def test_review_pr_correlation_id_persisted(client, clean_review_db):
    response = client.post(
        "/api/review/pr",
        json=ReviewRequest(repository="waste-iq/demo", pr_number=1).model_dump(),
        headers={"x-request-id": "my-correlation"},
    )
    session_id = response.json()["session_id"]
    detail = client.get(f"/api/review/sessions/{session_id}").json()
    assert detail["correlation_id"] == "my-correlation"
    assert detail["source"] == "api"
