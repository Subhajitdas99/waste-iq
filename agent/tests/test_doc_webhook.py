"""Tests for webhook-triggered Documentation Agent dispatch (Phase 4)."""

import base64
import json

import httpx
import pytest
import respx

from app.core.security import compute_webhook_signature

BASE = "https://api.github.com"
REPO = "waste-iq/waste-iq"
ANCHOR = "<!-- waste-iq-agent:doc-proposal v1 -->"
CHANGELOG = (
    "# Changelog\n\n"
    "## [Unreleased]\n\n"
    "### Added\n\n"
    "- **Old thing (#1)** — whatever.\n\n"
    "## [1.0.0] - 2026-01-01\n"
)


def _post(client, payload, event, action, delivery_id="deliv-docs-1"):
    body = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Delivery": delivery_id,
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": compute_webhook_signature(body, "test-webhook-secret"),
    }
    return client.post("/api/webhooks/github", content=body, headers=headers)


def _merged_pr_payload(action="closed", number=10):
    return {
        "action": action,
        "repository": {"full_name": REPO},
        "pull_request": {
            "number": number,
            "title": "feat(api): add notifications endpoint",
            "body": "Adds the endpoint and tests.",
            "merged": True,
            "base": {"ref": "develop"},
            "head": {"sha": "abc123"},
        },
    }


def _apply_comment_payload(number=10):
    return {
        "action": "created",
        "repository": {"full_name": REPO},
        "issue": {"number": number},
        "comment": {
            "body": "/agent docs apply",
            "html_url": f"https://github.com/waste-iq/waste-iq/pull/{number}#issuecomment-1",
        },
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


def _enable_docs_flags(monkeypatch, comments=True, patch_pr=False):
    from app.core.config import settings

    monkeypatch.setattr(settings, "agent_docs_auto_run", True)
    monkeypatch.setattr(settings, "agent_docs_comments_enabled", comments)
    monkeypatch.setattr(settings, "agent_docs_patch_pr_enabled", patch_pr)
    from app.agents.doc_service import DocService

    monkeypatch.setattr(DocService, "_installation_token", lambda self: "fake-token")


def _b64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def test_docs_dispatch_disabled_by_default(client, clean_runs_db):
    response = _post(client, _merged_pr_payload(), "pull_request", "closed")
    assert response.status_code == 202
    assert "docs" not in response.json()


def test_unmerged_pr_does_not_trigger_docs(client, clean_runs_db, monkeypatch):
    _enable_docs_flags(monkeypatch)
    payload = _merged_pr_payload()
    payload["pull_request"]["merged"] = False
    response = _post(client, payload, "pull_request", "closed")
    assert response.status_code == 202
    assert "docs" not in response.json()


def test_merged_pr_posts_proposal_comment(client, clean_runs_db, monkeypatch):
    _enable_docs_flags(monkeypatch)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/pulls/10/files?per_page=100").mock(
            return_value=httpx.Response(
                200,
                json=[{"filename": "backend/app/api/routes/auth.py"}],
            )
        )
        respx.get(f"{BASE}/repos/{REPO}/issues/10/comments?per_page=100").mock(
            return_value=httpx.Response(200, json=[])
        )
        post = respx.post(f"{BASE}/repos/{REPO}/issues/10/comments").mock(
            return_value=httpx.Response(201, json={"id": 50})
        )

        response = _post(client, _merged_pr_payload(), "pull_request", "closed")

    assert response.status_code == 202
    docs = response.json()["docs"]
    assert docs["comment_posted"] is True
    assert docs["changelog_section"] == "Added"
    body = json.loads(post.calls[0].request.content)
    assert ANCHOR in body["body"]
    assert "docs/API_SPECIFICATION.md" in body["body"]

    from app.db.models import AgentRun
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter(AgentRun.delivery_id == "deliv-docs-1").one()
        assert run.assistant == "docs"
        outcome = json.loads(run.outcome)
        assert outcome["pr_number"] == 10
        assert outcome["changelog_entry"].startswith("- **add notifications endpoint (#10)**")
    finally:
        db.close()


def test_merged_pr_proposal_is_idempotent(client, clean_runs_db, monkeypatch):
    _enable_docs_flags(monkeypatch)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/pulls/10/files?per_page=100").mock(
            return_value=httpx.Response(200, json=[])
        )
        respx.get(f"{BASE}/repos/{REPO}/issues/10/comments?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"body": f"{ANCHOR}\nproposal"}])
        )
        post = respx.post(f"{BASE}/repos/{REPO}/issues/10/comments").mock(
            return_value=httpx.Response(201, json={"id": 51})
        )

        response = _post(client, _merged_pr_payload(), "pull_request", "closed")

    assert response.status_code == 202
    assert response.json()["docs"]["comment_posted"] is False
    assert response.json()["docs"]["comment_skipped"] is True
    assert post.call_count == 0


def test_apply_command_opens_patch_pr(client, clean_runs_db, monkeypatch):
    _enable_docs_flags(monkeypatch, comments=True, patch_pr=True)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/issues/10/comments?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"body": f"{ANCHOR}\nproposal"}])
        )
        respx.get(f"{BASE}/repos/{REPO}/pulls/10").mock(
            return_value=httpx.Response(
                200,
                json={
                    "title": "feat(api): add notifications endpoint",
                    "base": {"ref": "develop", "sha": "base-sha"},
                    "head": {"sha": "head-sha"},
                },
            )
        )
        ref = respx.post(f"{BASE}/repos/{REPO}/git/refs").mock(
            return_value=httpx.Response(201, json={"ref": "refs/heads/agent/docs-10-20260806"})
        )
        contents = respx.get(
            f"{BASE}/repos/{REPO}/contents/CHANGELOG.md?ref=agent/docs-10-20260806"
        ).mock(
            return_value=httpx.Response(200, json={"content": _b64(CHANGELOG), "sha": "file-sha"})
        )
        update = respx.put(f"{BASE}/repos/{REPO}/contents/CHANGELOG.md").mock(
            return_value=httpx.Response(200, json={"content": {"sha": "new-sha"}})
        )
        pr = respx.post(f"{BASE}/repos/{REPO}/pulls").mock(
            return_value=httpx.Response(
                201,
                json={
                    "number": 101,
                    "html_url": "https://github.com/waste-iq/waste-iq/pull/101",
                    "base": {"ref": "develop"},
                    "head": {"ref": "agent/docs-10-20260806"},
                },
            )
        )

        response = _post(client, _apply_comment_payload(), "issue_comment", "created")

    assert response.status_code == 202
    docs = response.json()["docs"]
    assert docs["patch_pr_number"] == 101
    assert docs["branch"] == "agent/docs-10-20260806"
    assert ref.call_count == 1
    assert contents.call_count == 1
    assert update.call_count == 1
    updated = json.loads(update.calls[0].request.content)
    assert updated["branch"] == "agent/docs-10-20260806"
    assert updated["sha"] == "file-sha"
    new_changelog = base64.b64decode(updated["content"]).decode("utf-8")
    assert "add notifications endpoint (#10)" in new_changelog
    assert pr.call_count == 1
    pr_payload = json.loads(pr.calls[0].request.content)
    assert pr_payload["head"] == "agent/docs-10-20260806"
    assert pr_payload["base"] == "develop"

    from app.db.models import AgentRun
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter(AgentRun.delivery_id == "deliv-docs-1").one()
        assert run.assistant == "docs"
        assert run.status == "processed"
        outcome = json.loads(run.outcome)
        assert outcome["patch_pr_number"] == 101
    finally:
        db.close()


def test_apply_command_refused_without_proposal_anchor(client, clean_runs_db, monkeypatch):
    _enable_docs_flags(monkeypatch, patch_pr=True)
    with respx.mock:
        respx.get(f"{BASE}/repos/{REPO}/issues/10/comments?per_page=100").mock(
            return_value=httpx.Response(200, json=[{"body": "just a human comment"}])
        )
        ref = respx.post(f"{BASE}/repos/{REPO}/git/refs").mock(
            return_value=httpx.Response(201, json={})
        )

        response = _post(client, _apply_comment_payload(), "issue_comment", "created")

    assert response.status_code == 202
    docs = response.json()["docs"]
    assert docs["rejected"] == "no proposal anchor found"
    assert ref.call_count == 0

    from app.db.models import AgentRun
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter(AgentRun.delivery_id == "deliv-docs-1").one()
        assert run.status == "skipped"
    finally:
        db.close()


def test_apply_command_requires_patch_pr_enabled(client, clean_runs_db, monkeypatch):
    _enable_docs_flags(monkeypatch, comments=True, patch_pr=False)
    response = _post(client, _apply_comment_payload(), "issue_comment", "created")
    assert response.status_code == 202
    assert "docs" not in response.json()


def test_unknown_command_ignored(client, clean_runs_db, monkeypatch):
    _enable_docs_flags(monkeypatch, patch_pr=True)
    payload = _apply_comment_payload()
    payload["comment"]["body"] = "/agent something-else"
    response = _post(client, payload, "issue_comment", "created")
    assert response.status_code == 202
    assert "docs" not in response.json()
