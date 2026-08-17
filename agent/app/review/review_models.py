"""Pydantic models for the PR Review Agent (Phase 2).

The review agent analyzes pull requests against repository context and
produces evidence-backed findings. These models are the contract consumed
by the API and persisted by ReviewStore.
"""

from __future__ import annotations

from typing import Any, Literal, cast

from pydantic import BaseModel, Field

ReviewCategory = Literal[
    "correctness",
    "architecture",
    "security",
    "performance",
    "fastapi",
    "sqlalchemy",
    "react",
    "testing",
    "documentation",
]
Severity = Literal["critical", "high", "medium", "low", "info"]
FileStatus = Literal["added", "modified", "removed", "renamed", "copied", "unchanged"]

SEVERITY_RANK: dict[str, int] = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

REVIEW_CATEGORIES: tuple[str, ...] = (
    "correctness",
    "architecture",
    "security",
    "performance",
    "fastapi",
    "sqlalchemy",
    "react",
    "testing",
    "documentation",
)

DISCLAIMERS: list[str] = [
    "This review was produced by the Waste-IQ PR Review Agent and must be verified by a human "
    "before any action is taken.",
    "Findings are suggestions only — the agent never merges, approves, edits code, or comments on "
    "GitHub. Humans stay in charge of every decision.",
    "Every finding is grounded in repository evidence (files, ADRs, docs, roadmap, similar code). "
    "Anything without evidence is excluded rather than guessed.",
]


class DiffLine(BaseModel):
    kind: Literal["context", "added", "removed"]
    old_number: int | None = None
    new_number: int | None = None
    content: str = ""


class DiffHunk(BaseModel):
    header: str
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: list[DiffLine] = Field(default_factory=list)

    def added_lines(self) -> list[tuple[int, str]]:
        return [
            (line.new_number, line.content)
            for line in self.lines
            if line.kind == "added" and line.new_number is not None
        ]

    def new_side_lines(self) -> list[tuple[int, str]]:
        return [
            (line.new_number, line.content)
            for line in self.lines
            if line.kind in ("context", "added") and line.new_number is not None
        ]


class ChangedFile(BaseModel):
    path: str
    status: FileStatus = "modified"
    hunks: list[DiffHunk] = Field(default_factory=list)
    content: str | None = None

    @property
    def added_line_numbers(self) -> set[int]:
        if self.status == "added":
            return set(range(1, len((self.content or "").splitlines()) + 1))
        return {number for number, _ in self.added_lines}

    @property
    def added_lines(self) -> list[tuple[int, str]]:
        if self.status == "added" and self.content is not None:
            return list(enumerate(self.content.splitlines(), start=1))
        out: list[tuple[int, str]] = []
        for hunk in self.hunks:
            out.extend(hunk.added_lines())
        return out

    @property
    def new_content(self) -> str | None:
        if self.content is not None:
            return self.content
        if not self.hunks:
            return None
        lines: list[str] = []
        for hunk in self.hunks:
            lines.extend(content for _, content in hunk.new_side_lines())
        return "\n".join(lines)

    def snippet_around(self, line: int, radius: int = 3) -> str | None:
        content = self.new_content
        if content is None:
            return None
        lines = content.splitlines()
        if not lines:
            return None
        index = max(1, min(line, len(lines)))
        start = max(0, index - 1 - radius)
        end = min(len(lines), index - 1 + radius + 1)
        return "\n".join(lines[start:end])


class PullRequestData(BaseModel):
    number: int
    repo_full_name: str
    title: str = ""
    branch: str | None = None
    base_branch: str | None = None
    commit_sha: str | None = None
    author: str | None = None
    state: str | None = None
    diff: str | None = None
    files: list[ChangedFile] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class ContextReference(BaseModel):
    path: str
    start_line: int | None = None
    end_line: int | None = None
    section_title: str | None = None
    score: float = 0.0
    snippet: str | None = None
    source_type: str = "code"


class RepositoryContext(BaseModel):
    has_context: bool = False
    related_files: list[ContextReference] = Field(default_factory=list)
    related_docs: list[ContextReference] = Field(default_factory=list)
    related_adrs: list[ContextReference] = Field(default_factory=list)
    related_roadmap: list[ContextReference] = Field(default_factory=list)
    similar_code: list[ContextReference] = Field(default_factory=list)
    test_files_known: list[str] = Field(default_factory=list)


class FindingEvidence(BaseModel):
    kind: Literal["code", "context", "adr", "doc", "roadmap", "similar", "test", "coverage"]
    reference: str
    content: str | None = None
    confidence: float = 1.0


class ReviewFinding(BaseModel):
    rule_id: str
    category: ReviewCategory
    severity: Severity
    title: str
    explanation: str
    file_path: str
    start_line: int
    end_line: int
    snippet: str | None = None
    suggestion: str = ""
    confidence: float = 1.0
    related_adrs: list[str] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    evidence: list[FindingEvidence] = Field(default_factory=list)

    @property
    def reference(self) -> str:
        if self.start_line == self.end_line:
            return f"{self.file_path}:{self.start_line}"
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


class CategorySummary(BaseModel):
    category: ReviewCategory
    count: int = 0
    top_severity: Severity | None = None


class ReviewSummary(BaseModel):
    total: int = 0
    counts_by_category: dict[str, int] = Field(default_factory=dict)
    counts_by_severity: dict[str, int] = Field(default_factory=dict)
    categories: list[CategorySummary] = Field(default_factory=list)

    @classmethod
    def build(cls, findings: list[ReviewFinding]) -> ReviewSummary:
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        category_severity: dict[str, set[str]] = {}
        for finding in findings:
            by_category[finding.category] = by_category.get(finding.category, 0) + 1
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
            category_severity.setdefault(finding.category, set()).add(finding.severity)
        categories: list[CategorySummary] = []
        for name in REVIEW_CATEGORIES:
            count = by_category.get(name, 0)
            if count == 0:
                continue
            severities = category_severity.get(name, set())
            top = (
                max(severities, key=lambda severity: SEVERITY_RANK.get(severity, 0))
                if severities
                else None
            )
            categories.append(
                CategorySummary(
                    category=cast(ReviewCategory, name),
                    count=count,
                    top_severity=cast(Severity, top) if top else None,
                )
            )
        categories.sort(key=lambda item: SEVERITY_RANK[item.top_severity or "info"], reverse=True)
        return cls(
            total=len(findings),
            counts_by_category=by_category,
            counts_by_severity=by_severity,
            categories=categories,
        )


class ReviewMetrics(BaseModel):
    files_analyzed: int = 0
    added_lines: int = 0
    context_queries: int = 0
    references_retrieved: int = 0
    duration_ms: int = 0


class PRReview(BaseModel):
    engine_version: str
    session_id: int | None = None
    repo_full_name: str
    pr_number: int
    branch: str | None = None
    base_branch: str | None = None
    commit_sha: str | None = None
    title: str = ""
    author: str | None = None
    source: str = "api"
    summary: ReviewSummary
    findings: list[ReviewFinding]
    repository_context: RepositoryContext
    metrics: ReviewMetrics
    correlation_id: str | None = None
    generated_at: str = ""
    disclaimers: list[str] = Field(default_factory=lambda: list(DISCLAIMERS))


class ReviewRequest(BaseModel):
    repository: str = Field(min_length=1, max_length=256)
    pr_number: int = Field(ge=1)
    branch: str | None = Field(default=None, max_length=256)
    source: str = "api"


class ReviewStatus(BaseModel):
    healthy: bool = True
    enabled: bool = True
    engine_version: str = ""
    total_sessions: int = 0
    pending: int = 0
    completed: int = 0
    failed: int = 0
    findings_total: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)
    average_duration_ms: int = 0


class ReviewUnavailable(Exception):
    """Raised when a PR cannot be fetched or reviewed (no network / not found)."""


class ReviewError(Exception):
    """Raised when a review run fails after the session was recorded."""
