"""Tests for webhook-triggered Issue Assistant dispatch (Phase 3)."""

import json

import httpx
import pytest
import respx

from app.core.security import compute_webhook_signature

BASE = "https://api.github.com"
REPO = "waste-iq/waste-iq"
ANCHOR = "<!-- waste-iq-agent:issue-triage v1 -->"


def _post(client, payload, event, action, delivery_id="deliv-issue-1"):
    body = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Delivery": delivery_id,
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": compute_webhook_signature(body, "test-webhook-secret"),
    }
    return client.post("/api/webhooks/github", content=body, headers=headers)


def _issue_payload(action, number=1, title="Login API broken", body="Login fails"):
    return {
        "action": action,
        "repository": {"full_name": REPO},
        "issue": {"number": number, "title": title, "body": body},
    }


@pytest.fixture
def clean_runs_db():
    from sqlalchemy import delete

    from app.db.models import AgentRun, AuditLogEntry
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        for model in (AgentRun, AuditLogEntry):
            db.execute(delete(model))
        db.commit()
    finally:
        db.close()


def _enable_issue_flags(monkeypatch, comments=True):
    from app.core.config import settings

    monkeypatch.setattr(settings, "agent_issue_auto_run", True)
    monkeypatch.setattr(settings, "agent_issue_comments_enabled", comments)
    from app.agents.issue_service import IssueService

    monkeypatch.setattr(IssueService, "_installation_token", lambda self: "fake-token")


def _comment_body():
    return f"{ANCHOR}\n\n### AI Agent triage (propose-only)\n"


def test_issues_opened_dispatches_triage_and_posts_comment(client, clean_runs_db, monkeypatch):
    _enable_issue_flags(monkeypatch)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/issues?state=open&per_page=30").mock(
            return_value=httpx.Response(200, json=[{"number": 3, "title": "Other", "body": ""}])
        )
        respx.get(f"{BASE}/repos/{REPO}/labels?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"name": "bug"}, {"name": "backend"}])
        )
        respx.get(f"{BASE}/repos/{REPO}/issues/1/comments?per_page=100").mock(
            return_value=httpx.Response(200, json=[])
        )
        post = respx.post(f"{BASE}/repos/{REPO}/issues/1/comments").mock(
            return_value=httpx.Response(201, json={"id": 42})
        )

        response = _post(client, _issue_payload("opened"), "issues", "opened")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    issue = data["issue"]
    assert issue["issue_number"] == 1
    assert issue["comment_posted"] is True
    assert "bug" in issue["labels"]
    assert post.call_count == 1
    assert post.calls[0].request.content

    from app.db.models import AgentRun
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter(AgentRun.delivery_id == "deliv-issue-1").one()
        assert run.assistant == "issue"
        assert run.status == "processed"
        outcome = json.loads(run.outcome)
        assert outcome["issue_number"] == 1
        assert outcome["comment_posted"] is True
    finally:
        db.close()


def test_issues_opened_dispatches_triage_without_comments(client, clean_runs_db, monkeypatch):
    _enable_issue_flags(monkeypatch, comments=False)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/issues?state=open&per_page=30").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{BASE}/repos/{REPO}/labels?per_page=100").mock(
            return_value=httpx.Response(200, json=[])
        )

        response = _post(client, _issue_payload("opened"), "issues", "opened")

    assert response.status_code == 202
    issue = response.json()["issue"]
    assert issue["comment_posted"] is False
    assert issue["priority"] == "high"


def test_issues_dispatch_disabled_by_default(client, clean_runs_db):
    response = _post(client, _issue_payload("opened"), "issues", "opened")
    assert response.status_code == 202
    assert "issue" not in response.json()


def test_duplicate_delivery_posts_comment_once(client, clean_runs_db, monkeypatch):
    _enable_issue_flags(monkeypatch)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/issues?state=open&per_page=30").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{BASE}/repos/{REPO}/labels?per_page=100").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{BASE}/repos/{REPO}/issues/1/comments?per_page=100").mock(
            side_effect=[
                httpx.Response(200, json=[]),
                httpx.Response(200, json=[{"body": _comment_body()}]),
            ]
        )
        post = respx.post(f"{BASE}/repos/{REPO}/issues/1/comments").mock(
            return_value=httpx.Response(201, json={"id": 43})
        )

        first = _post(client, _issue_payload("opened"), "issues", "opened")
        second = _post(client, _issue_payload("opened"), "issues", "opened")

    assert first.status_code == 202 and second.status_code == 202
    assert first.json()["issue"]["comment_posted"] is True
    assert second.json()["issue"]["comment_posted"] is False
    assert post.call_count == 1


def test_existing_triage_comment_is_not_duplicated(client, clean_runs_db, monkeypatch):
    _enable_issue_flags(monkeypatch)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/issues?state=open&per_page=30").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{BASE}/repos/{REPO}/labels?per_page=100").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{BASE}/repos/{REPO}/issues/1/comments?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"body": _comment_body()}])
        )
        post = respx.post(f"{BASE}/repos/{REPO}/issues/1/comments").mock(
            return_value=httpx.Response(201, json={"id": 44})
        )

        response = _post(client, _issue_payload("opened"), "issues", "opened")

    assert response.status_code == 202
    assert response.json()["issue"]["comment_posted"] is False
    assert response.json()["issue"]["comment_skipped"] is True
    assert post.call_count == 0


def test_pull_request_event_does_not_trigger_issue_triage(client, clean_runs_db, monkeypatch):
    _enable_issue_flags(monkeypatch)
    payload = {
        "action": "opened",
        "repository": {"full_name": REPO},
        "pull_request": {"number": 5},
    }
    response = _post(client, payload, "pull_request", "opened")
    assert response.status_code == 202
    assert "issue" not in response.json()
