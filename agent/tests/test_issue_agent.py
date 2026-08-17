"""Unit tests for the Issue Assistant (Phase 3): triage + comment format."""

import pytest

from app.agents.issue_agent import IssueAssistant, format_comment
from app.context.di import Container

AUTH_ROUTE = """\
from fastapi import APIRouter

router = APIRouter(prefix="/api/auth")


@router.post("/login")
async def login(username: str, password: str):
    return {"ok": True}
"""

ROADMAP_DOC = """# Waste-IQ V1 Roadmap

## Milestone M0 (WIQ-V1-003)

Issue Assistant: triage comments on new issues.
"""


@pytest.fixture
def container(tmp_path, clean_context_db):
    from app.db.session import SessionLocal

    (tmp_path / "backend" / "app" / "api" / "routes").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (tmp_path / "backend" / "app" / "api" / "routes" / "auth.py").write_text(
        AUTH_ROUTE, encoding="utf-8"
    )
    (tmp_path / "docs" / "architecture" / "AI_ENGINEERING_AGENT.md").write_text(
        ROADMAP_DOC, encoding="utf-8"
    )
    container = Container(
        SessionLocal,
        repository_root=tmp_path,
        min_tokens=50,
        max_tokens=500,
    )
    container.pipeline().run()
    return container


def _issue(number=1, title="Fix the login flow", body="Login returns an error for dealers."):
    return {"number": number, "title": title, "body": body}


def test_analyze_suggests_backend_and_bug_labels(container):
    triage = IssueAssistant(container).analyze(
        _issue(title="Login API returns a broken error"),
        repo_labels=["bug", "backend", "frontend", "security"],
    )
    assert "bug" in triage.suggested_labels
    assert "backend" in triage.suggested_labels
    assert triage.suggested_labels[0] == "bug"


def test_analyze_filters_labels_to_repo_labels(container):
    triage = IssueAssistant(container).analyze(
        _issue(title="Login API broken"),
        repo_labels=["frontend"],
    )
    assert triage.suggested_labels == []


def test_analyze_offline_keeps_raw_label_suggestions(container):
    triage = IssueAssistant(container).analyze(_issue(title="Login API broken"))
    assert "bug" in triage.suggested_labels


def test_analyze_priority_critical_for_security_issue(container):
    triage = IssueAssistant(container).analyze(
        _issue(title="SQL injection vulnerability in search")
    )
    assert triage.priority == "critical"


def test_analyze_priority_high_for_bug_issue(container):
    triage = IssueAssistant(container).analyze(_issue(title="Regression: pickup fails"))
    assert triage.priority == "high"


def test_analyze_priority_default_medium(container):
    triage = IssueAssistant(container).analyze(_issue(title="Add a settings page", body=""))
    assert triage.priority == "medium"


def test_analyze_milestone_detected_from_roadmap_evidence(container):
    triage = IssueAssistant(container).analyze(
        _issue(title="Issue assistant triage comments"),
        repo_labels=[],
    )
    assert triage.milestone in ("M0", "WIQ-V1-003")


def test_analyze_evidence_collected_from_repo(container):
    triage = IssueAssistant(container).analyze(_issue(title="Login returns an error"))
    assert any(item.path.endswith("auth.py") for item in triage.evidence)
    for item in triage.evidence:
        assert item.path and item.start_line >= 1


def test_analyze_duplicate_detection_finds_similar_issue(container):
    open_issues = [
        {"number": 9, "title": "Fix login error for dealers", "body": "login is broken"},
        {"number": 8, "title": "Add dark mode", "body": "css colors"},
    ]
    triage = IssueAssistant(container).analyze(
        _issue(number=1, title="Fix login error for dealers", body="login is broken"),
        open_issues=open_issues,
    )
    assert triage.duplicate_of and triage.duplicate_of[0]["number"] == 9


def test_analyze_duplicate_detection_ignores_self(container):
    open_issues = [{"number": 1, "title": "Fix login error", "body": "login broken"}]
    triage = IssueAssistant(container).analyze(
        _issue(number=1, title="Fix login error", body="login broken"),
        open_issues=open_issues,
    )
    assert triage.duplicate_of == []


def test_analyze_duplicate_detection_offline_returns_empty(container):
    triage = IssueAssistant(container).analyze(_issue())
    assert triage.duplicate_of == []


def test_format_comment_contains_anchor_and_evidence(container):
    triage = IssueAssistant(container).analyze(_issue(title="Login returns an error"))
    body = format_comment(triage)
    assert body.startswith("<!-- waste-iq-agent:issue-triage v1 -->")
    assert "propose-only" in body.lower()
    assert "nothing was modified" in body
    assert "Evidence" in body
    assert "auth.py" in body


def test_format_comment_shows_duplicates(container):
    triage = IssueAssistant(container).analyze(
        _issue(title="Fix login error", body="login broken"),
        open_issues=[{"number": 7, "title": "Fix login error", "body": "login broken"}],
    )
    body = format_comment(triage)
    assert "#7" in body
    assert "Possible duplicates" in body
