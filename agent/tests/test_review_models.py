"""Tests for review models."""

from app.review.review_models import (
    ChangedFile,
    DiffHunk,
    DiffLine,
    ReviewFinding,
    ReviewSummary,
    SEVERITY_RANK,
)


def _finding(rule_id, category, severity, start=1, end=1):
    return ReviewFinding(
        rule_id=rule_id,
        category=category,
        severity=severity,
        title="t",
        explanation="e",
        file_path="f.py",
        start_line=start,
        end_line=end,
    )


def test_changed_file_added_lines_from_content():
    file = ChangedFile(path="a.py", status="added", content="one\ntwo\nthree")
    assert file.added_lines == [(1, "one"), (2, "two"), (3, "three")]
    assert file.added_line_numbers == {1, 2, 3}


def test_changed_file_modified_lines_from_hunks():
    hunk = DiffHunk(
        header="@@ -1 +1 @@",
        old_start=1,
        old_lines=1,
        new_start=10,
        new_lines=2,
        lines=[
            DiffLine(kind="context", old_number=1, new_number=10, content="c"),
            DiffLine(kind="added", new_number=11, content="n"),
            DiffLine(kind="removed", old_number=2, content="r"),
        ],
    )
    file = ChangedFile(path="a.py", status="modified", hunks=[hunk])
    assert file.added_lines == [(11, "n")]
    assert file.added_line_numbers == {11}
    assert file.new_content == "c\nn"
    assert file.snippet_around(11) == "c\nn"
    assert file.snippet_around(11, radius=0) == "n"


def test_snippet_around_bounds():
    file = ChangedFile(path="a.py", status="added", content="a\nb\nc\nd\ne")
    assert file.snippet_around(1) == "a\nb\nc\nd"
    assert file.snippet_around(5) == "b\nc\nd\ne"
    assert file.snippet_around(3) == "a\nb\nc\nd\ne"


def test_severity_rank_ordering():
    assert SEVERITY_RANK["critical"] > SEVERITY_RANK["high"]
    assert SEVERITY_RANK["low"] > SEVERITY_RANK["info"]


def test_review_summary_build():
    findings = [
        _finding("R1", "security", "critical"),
        _finding("R2", "security", "high"),
        _finding("R3", "correctness", "low"),
    ]
    summary = ReviewSummary.build(findings)
    assert summary.total == 3
    assert summary.counts_by_category == {"security": 2, "correctness": 1}
    assert summary.counts_by_severity == {"critical": 1, "high": 1, "low": 1}
    names = [c.category for c in summary.categories]
    assert names == ["security", "correctness"]
    assert summary.categories[0].top_severity == "critical"


def test_review_summary_build_empty():
    summary = ReviewSummary.build([])
    assert summary.total == 0
    assert summary.categories == []


def test_review_summary_ignores_absent_categories():
    findings = [_finding("R1", "react", "low")]
    summary = ReviewSummary.build(findings)
    assert summary.categories == [summary.categories[0]]
    assert summary.categories[0].category == "react"
