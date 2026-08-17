"""Human-readable formatting of review objects (console + markdown)."""

from __future__ import annotations

from app.review.review_models import PRReview, ReviewFinding


def finding_reference(finding: ReviewFinding) -> str:
    """A single-line evidence reference, e.g.

    File: backend/services/pickup_service.py, Lines: 102-119, Confidence: 0.93
    """
    parts = [f"File: {finding.file_path}", f"Lines: {finding.start_line}-{finding.end_line}"]
    if finding.related_adrs:
        parts.append(f"Related ADR: {', '.join(finding.related_adrs[:2])}")
    if finding.related_files:
        parts.append(f"Related: {', '.join(finding.related_files[:3])}")
    parts.append(f"Confidence: {finding.confidence:.2f}")
    return ", ".join(parts)


def format_finding(finding: ReviewFinding) -> str:
    lines = [
        f"[{finding.severity.upper()}] {finding.title} ({finding.rule_id}, {finding.category})",
        f"  {finding.explanation}",
        f"  {finding_reference(finding)}",
    ]
    if finding.suggestion:
        lines.append(f"  Suggested fix: {finding.suggestion}")
    if finding.snippet:
        snippet = "\n".join("  | " + line for line in finding.snippet.splitlines()[:8])
        lines.append(snippet)
    return "\n".join(lines)


def format_review(review: PRReview) -> str:
    """Format an entire review as markdown for a human reviewer."""
    header = (
        f"# PR Review: {review.repo_full_name}#{review.pr_number} "
        f"({review.engine_version})\n"
        f"- {review.title}\n"
        f"- Branch {review.branch or '?'} -> {review.base_branch or '?'} "
        f"@{review.commit_sha or '?'}\n"
        f"- {review.summary.total} findings "
        f"({_severity_line(review)})\n"
    )
    sections = [header]
    for finding in review.findings:
        sections.append(format_finding(finding))
    if not review.findings:
        sections.append("No findings. This change looks clean per the rule set.")
    sections.append("\n## Disclaimer\n")
    sections.extend(f"- {disclaimer}" for disclaimer in review.disclaimers)
    return "\n\n".join(sections)


def concise_summary(review: PRReview) -> str:
    by_cat = ", ".join(
        f"{cat}={count}" for cat, count in sorted(review.summary.counts_by_category.items())
    )
    return (
        f"{review.repo_full_name}#{review.pr_number}: {review.summary.total} findings "
        f"({_severity_line(review)}; {by_cat})"
    )


def _severity_line(review: PRReview) -> str:
    counts = review.summary.counts_by_severity
    return ", ".join(
        f"{severity}={counts[severity]}"
        for severity in ("critical", "high", "medium", "low", "info")
        if counts.get(severity)
    )
