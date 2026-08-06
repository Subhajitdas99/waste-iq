"""Issue Assistant — triage suggestions for new issues (Phase 3).

Propose-only: the assistant never changes labels, milestones, or issue
state. Its only possible write is a comment, and that is gated by
``AGENT_ISSUE_COMMENTS_ENABLED`` (default off) plus an idempotency
anchor check (never post twice for the same issue state).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

from app.context.tokenizer import subword_tokens

# Keyword -> suggested label (applied in rule order, deduplicated).
LABEL_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("bug", ("bug", "crash", "exception", "broken", "regression", "fails", "failed")),
    ("security", ("security", "vulnerability", "xss", "injection", "password", "cve")),
    ("performance", ("performance", "slow", "latency", "optimize", "optimisation", "timeout")),
    ("frontend", ("react", "component", "ui", "css", "frontend", "typescript")),
    ("backend", ("api", "endpoint", "backend", "service", "database", "sql")),
    ("documentation", ("documentation", "docs", "readme")),
    ("testing", ("test", "coverage", "pytest", "vitest")),
    ("ci", ("ci", "workflow", "build", "github actions")),
    ("dependencies", ("dependency", "upgrade", "version bump", "requirements")),
    ("enhancement", ("feature", "enhancement", "improve", "support")),
    ("roadmap", ("milestone", "roadmap", "wiq-v1")),
]

PRIORITY_RULES: list[tuple[str, int, tuple[str, ...]]] = [
    ("critical", 4, ("security", "vulnerability", "crash", "urgent", "critical", "blocked", "p0")),
    ("high", 3, ("bug", "broken", "regression", "fails", "error", "p1")),
    ("low", 1, ("minor", "cosmetic", "typo", "nice to have", "p3", "later")),
]
_PRIORITY_DEFAULT = "medium"

_MILESTONE_RE = re.compile(r"(WIQ-V1-\d{3})|\b(M\d)\b", re.IGNORECASE)

_COMMENT_ANCHOR = "<!-- waste-iq-agent:issue-triage v1 -->"


class TriageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    start_line: int
    end_line: int
    section_title: str | None = None
    score: float


class IssueTriage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_number: int
    title: str
    suggested_labels: list[str] = []
    priority: str = _PRIORITY_DEFAULT
    milestone: str | None = None
    duplicate_of: list[dict] = []
    summary: str = ""
    evidence: list[TriageEvidence] = []


class IssueAssistant:
    """Deterministic triage: labels, priority, milestone, duplicates, evidence.

    Fully offline-capable: labels/duplicates enrichment is skipped when no
    open-issue/label data is provided (e.g. GitHub is not configured).
    """

    def __init__(self, container=None) -> None:
        self._container = container

    @property
    def container(self):
        if self._container is None:
            from app.api.dependencies import get_container

            self._container = get_container()
        return self._container

    def analyze(
        self,
        issue: dict,
        *,
        open_issues: list[dict] | None = None,
        repo_labels: list[str] | None = None,
        evidence_limit: int = 6,
    ) -> IssueTriage:
        number = int(issue.get("number") or 0)
        title = issue.get("title") or ""
        body = issue.get("body") or ""
        text = f"{title}\n{body}".lower()

        triage = IssueTriage(issue_number=number, title=title)
        triage.suggested_labels = self._suggest_labels(text, repo_labels)
        triage.priority = self._suggest_priority(text)
        triage.evidence = self._collect_evidence(f"{title}\n{body}", evidence_limit)
        triage.milestone = self._suggest_milestone(triage.evidence)
        triage.duplicate_of = self._find_duplicates(number, title, body, open_issues or [])
        triage.summary = self._summarize(title, body, triage)
        return triage

    # ------------------------------------------------------------------
    def _suggest_labels(self, text: str, repo_labels: list[str] | None) -> list[str]:
        suggested: list[str] = []
        for label, keywords in LABEL_RULES:
            if label in suggested:
                continue
            if any(keyword in text for keyword in keywords):
                suggested.append(label)
        if repo_labels:
            existing = {name.lower(): name for name in repo_labels}
            suggested = [
                existing.get(label, label) for label in suggested if label.lower() in existing
            ]
        return suggested

    def _suggest_priority(self, text: str) -> str:
        score = 0
        for level, weight, keywords in PRIORITY_RULES:
            if any(keyword in text for keyword in keywords):
                score = max(score, weight)
        for level, weight, keywords in PRIORITY_RULES:
            if weight == score:
                return level
        return _PRIORITY_DEFAULT

    def _collect_evidence(self, query: str, limit: int) -> list[TriageEvidence]:
        from app.context.models import SearchRequest

        try:
            response = self.container.search_service().hybrid_search(
                SearchRequest(query=query, limit=limit)
            )
        except Exception:  # noqa: BLE001 - evidence is best-effort
            return []
        return [
            TriageEvidence(
                path=result.path,
                start_line=result.start_line,
                end_line=result.end_line,
                section_title=result.section_title,
                score=result.score,
            )
            for result in response.results
        ]

    def _suggest_milestone(self, evidence: list[TriageEvidence]) -> str | None:
        for item in evidence:
            searchable = " ".join(part for part in (item.path, item.section_title or ""))
            match = _MILESTONE_RE.search(searchable)
            if match:
                return (match.group(1) or match.group(2)).upper()
        return None

    def _find_duplicates(
        self, number: int, title: str, body: str, open_issues: list[dict]
    ) -> list[dict]:
        if not open_issues:
            return []
        from app.core.config import settings

        threshold = settings.agent_issue_duplicate_threshold
        max_duplicates = settings.agent_issue_max_duplicates
        self_terms = set(subword_tokens(f"{title} {body}"))
        if not self_terms:
            return []
        embedder = self.container.embedder
        self_vec = embedder.embed([f"{title} {body}"])[0]

        scored: list[tuple[float, dict]] = []
        for candidate in open_issues:
            other_number = int(candidate.get("number") or 0)
            if other_number == number:
                continue
            other_title = candidate.get("title") or ""
            other_body = candidate.get("body") or ""
            other_terms = set(subword_tokens(f"{other_title} {other_body}"))
            if not other_terms:
                continue
            jaccard = len(self_terms & other_terms) / len(self_terms | other_terms)
            other_vec = embedder.embed([f"{other_title} {other_body}"])[0]
            cosine = _cosine(self_vec, other_vec)
            similarity = 0.5 * jaccard + 0.5 * cosine
            if similarity >= threshold:
                scored.append(
                    (similarity, {"number": other_number, "similarity": round(similarity, 3)})
                )
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:max_duplicates]]

    def _summarize(self, title: str, body: str, triage: IssueTriage) -> str:
        words = len(body.split())
        return (
            f"{words} words in the description. "
            f"Triage: priority {triage.priority}, "
            f"{len(triage.suggested_labels)} label suggestion(s), "
            f"{len(triage.duplicate_of)} possible duplicate(s)."
        )


def format_comment(triage: IssueTriage) -> str:
    """Propose-only comment body with an idempotency anchor."""
    lines = [
        _COMMENT_ANCHOR,
        "### AI Agent triage (propose-only)",
        "",
        "**Suggested labels:** "
        + (", ".join(f"`{label}`" for label in triage.suggested_labels) or "_none_"),
        f"**Priority:** {triage.priority}",
        f"**Milestone:** {triage.milestone or '_none detected_'}",
        "",
        triage.summary,
    ]
    if triage.duplicate_of:
        lines += [
            "",
            "**Possible duplicates:**",
        ]
        for dup in triage.duplicate_of:
            lines.append(f"- #{dup['number']} (similarity {dup['similarity']:.0%})")
    if triage.evidence:
        lines += ["", "**Evidence:**"]
        for item in triage.evidence[:5]:
            section = f" ({item.section_title})" if item.section_title else ""
            citation = f"`{item.path}:{item.start_line}-{item.end_line}`"
            lines.append(f"- {citation}{section} (score {item.score:.3f})")
    lines += [
        "",
        "_Automated proposal only — nothing was modified on this issue._",
    ]
    return "\n".join(lines)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    if dot <= 0:
        return 0.0
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)
