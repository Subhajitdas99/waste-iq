"""Tests for the human-readable review formatter."""

from app.review.review_models import (
    PRReview,
    RepositoryContext,
    ReviewFinding,
    ReviewMetrics,
    ReviewSummary,
)
from app.review.review_formatter import (
    concise_summary,
    finding_reference,
    format_finding,
    format_review,
)


def _finding(**overrides) -> ReviewFinding:
    values = dict(
        rule_id="CORR-PY-EXCEPT",
        category="correctness",
        severity="medium",
        title="Bare except",
        explanation="A bare except catches everything.",
        file_path="app/x.py",
        start_line=3,
        end_line=5,
        snippet="try:\n    pass\nexcept:\n    pass",
        suggestion="Use `except Exception`.",
        confidence=0.91,
        related_adrs=["ADR-001"],
        related_files=["app/y.py"],
    )
    values.update(overrides)
    return ReviewFinding(**values)


def _review() -> PRReview:
    findings = [_finding(), _finding(rule_id="SEC-EVAL", category="security", severity="critical")]
    return PRReview(
        engine_version="2.0.0",
        repo_full_name="waste-iq/demo",
        pr_number=1,
        branch="feature/x",
        base_branch="main",
        commit_sha="abcd",
        title="Demo PR",
        summary=ReviewSummary.build(findings),
        findings=findings,
        repository_context=RepositoryContext(),
        metrics=ReviewMetrics(files_analyzed=2),
    )


def test_finding_reference_includes_file_and_lines():
    ref = finding_reference(_finding())
    assert "File: app/x.py" in ref
    assert "Lines: 3-5" in ref
    assert "Confidence: 0.91" in ref


def test_finding_reference_omits_related_when_empty():
    ref = finding_reference(_finding(related_adrs=[], related_files=[]))
    assert "Related" not in ref


def test_format_finding_includes_severity_rule_and_snippet():
    block = format_finding(_finding())
    assert "[MEDIUM]" in block
    assert "CORR-PY-EXCEPT" in block
    assert "correctness" in block
    assert "| try:" in block
    assert "Suggested fix" in block


def test_format_review_renders_header_findings_disclaimers():
    block = format_review(_review())
    assert "# PR Review: waste-iq/demo#1 (2.0.0)" in block
    assert "3 findings" not in block
    assert "[CRITICAL]" in block
    assert "## Disclaimer" in block
    assert "grounded in repository evidence" in block


def test_format_review_no_findings_message():
    review = _review()
    review.findings = []
    block = format_review(review)
    assert "No findings." in block


def test_concise_summary_line():
    line = concise_summary(_review())
    assert line.startswith("waste-iq/demo#1: 2 findings")
    assert "critical=1" in line
    assert "medium=1" in line
    assert "correctness=1" in line
    assert "security=1" in line
