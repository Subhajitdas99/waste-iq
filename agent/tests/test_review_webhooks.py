"""Tests for webhook-triggered review dispatch."""

import json

from app.core.security import compute_webhook_signature


def _post(client, payload, event, action, delivery_id="deliv-9"):
    body = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Delivery": delivery_id,
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": compute_webhook_signature(body, "test-webhook-secret"),
    }
    return client.post("/api/webhooks/github", content=body, headers=headers)


def _pr_payload(action, number=1, repo="waste-iq/demo", **extra):
    return {
        "action": action,
        "repository": {"full_name": repo},
        "pull_request": {"number": number},
        **extra,
    }


def test_webhook_pull_request_opened_triggers_review(client, clean_review_db):
    response = _post(client, _pr_payload("opened"), "pull_request", "opened")
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "delivery_id" in data
    assert "review" in data
    assert data["review"]["session_id"] is not None
    assert data["review"]["findings_count"] > 0


def test_webhook_pull_request_synchronize_triggers_review(client, clean_review_db):
    response = _post(
        client, _pr_payload("synchronize"), "pull_request", "synchronize", delivery_id="deliv-s"
    )
    assert response.status_code == 202
    assert "review" in response.json()
    assert response.json()["review"]["session_id"] is not None


def test_webhook_issues_event_does_not_trigger_review(client, clean_review_db):
    response = _post(client, {"action": "opened", "issue": {"number": 5}}, "issues", "opened")
    assert response.status_code == 202
    assert "review" not in response.json()


def test_webhook_non_demo_repo_not_triggered(client, clean_review_db, monkeypatch):
    from app.review import review_service as rs
    from app.review.review_models import ReviewUnavailable

    def no_token(self):
        raise ReviewUnavailable("no token available")

    monkeypatch.setattr(rs.ReviewService, "_installation_token", no_token)
    response = _post(
        client,
        _pr_payload("opened", repo="other/org"),
        "pull_request",
        "opened",
        delivery_id="deliv-other",
    )
    assert response.status_code == 202
    assert "review" not in response.json()


def test_webhook_workflow_run_completed_triggers_review(client, clean_review_db):
    payload = {
        "action": "completed",
        "repository": {"full_name": "waste-iq/demo"},
        "workflow_run": {"head_branch": "feature/demo-payments"},
    }
    response = _post(client, payload, "workflow_run", "completed", delivery_id="deliv-w")
    assert response.status_code == 202
    data = response.json()
    assert "review" in data
    assert data["review"]["session_id"] is not None


def test_webhook_review_failure_does_not_fail_ack(client, clean_review_db, monkeypatch):
    from app.review import review_service as rs

    def broken_event(self, envelope):
        raise RuntimeError("nope")

    monkeypatch.setattr(rs.ReviewService, "review_event", broken_event)
    response = _post(client, _pr_payload("opened"), "pull_request", "opened", delivery_id="deliv-x")
    assert response.status_code == 202
    assert "review" not in response.json()
