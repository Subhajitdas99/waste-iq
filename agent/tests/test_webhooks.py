import json

from app.core.security import compute_webhook_signature


def _headers(payload, delivery_id="abc-123", event="issues", action="opened"):
    body = json.dumps(payload).encode()
    return body, {
        "X-GitHub-Delivery": delivery_id,
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": compute_webhook_signature(body, "test-webhook-secret"),
    }


def test_valid_event_accepted(client):
    body, headers = _headers({"action": "opened", "issue": {"number": 44}})
    response = client.post("/api/webhooks/github", content=body, headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["delivery_id"] == "abc-123"


def test_invalid_signature_rejected(client):
    body = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/api/webhooks/github",
        content=body,
        headers={"X-GitHub-Delivery": "x", "X-GitHub-Event": "issues"},
    )
    assert response.status_code == 401


def test_tampered_signature_rejected(client):
    body, headers = _headers({"action": "opened"}, delivery_id="abc-1")
    headers["X-Hub-Signature-256"] = "sha256=0000"
    response = client.post("/api/webhooks/github", content=body, headers=headers)
    assert response.status_code == 401


def test_malformed_body_rejected(client):
    body = b"not json"
    headers = {"X-Hub-Signature-256": compute_webhook_signature(body, "test-webhook-secret")}
    response = client.post("/api/webhooks/github", content=body, headers=headers)
    assert response.status_code == 400


def test_missing_delivery_rejected(client):
    body, headers = _headers({"action": "opened"})
    headers.pop("X-GitHub-Delivery")
    response = client.post("/api/webhooks/github", content=body, headers=headers)
    assert response.status_code == 400


def test_duplicate_delivery_recorded_once(client):
    from app.db.session import SessionLocal
    from app.db.models import AgentRun

    body, headers = _headers({"action": "opened"}, delivery_id="dup-42")
    first = client.post("/api/webhooks/github", content=body, headers=headers)
    second = client.post("/api/webhooks/github", content=body, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 202

    db = SessionLocal()
    try:
        count = db.query(AgentRun).filter(AgentRun.delivery_id == "dup-42").count()
        run = db.query(AgentRun).filter(AgentRun.delivery_id == "dup-42").one()
    finally:
        db.close()

    assert count == 1
    assert run.event_type == "issues"
    assert run.event_action == "opened"
    assert run.status == "processed"
