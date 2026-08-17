"""Documentation Agent — changelog + doc drift proposals for merged PRs (Phase 4).

Propose-only: the agent never writes to the repository directly. Its only
outputs are (a) an anchored proposal comment on the merged PR and (b) — after
explicit human approval via the ``/agent docs apply`` command and with
``AGENT_DOCS_PATCH_PR_ENABLED`` — a patch PR on an ``agent/docs-*`` branch.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict

# Conventional-commit type -> Keep a Changelog section.
_CHANGELOG_SECTIONS: list[tuple[str, str]] = [
    ("feat", "Added"),
    ("fix", "Fixed"),
    ("perf", "Changed"),
    ("refactor", "Changed"),
    ("build", "Changed"),
    ("ci", "Changed"),
    ("chore", "Changed"),
    ("deprecate", "Deprecated"),
    ("remove", "Removed"),
    ("security", "Security"),
    ("docs", "Documented"),
]
_SECTION_ORDER = [
    "Added",
    "Changed",
    "Deprecated",
    "Removed",
    "Fixed",
    "Security",
    "Documented",
]

_CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|perf|refactor|build|ci|chore|deprecate|remove|security|docs)(?:\(([^)]+)\))?:\s*(.*)$",
    re.IGNORECASE,
)

# Changed-code subtree -> tracked doc that may need a sync update.
DOC_DRIFT_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    (
        "docs/API_SPECIFICATION.md",
        "API surface",
        ("backend/app/api", "backend/app/routes", "routes.py", "endpoints"),
    ),
    (
        "docs/DATABASE_SCHEMA.md",
        "database schema",
        ("backend/app/models", "models/", "migrations", "alembic", "schemas"),
    ),
    (
        "docs/SYSTEM_ARCHITECTURE.md",
        "system architecture",
        ("backend/app/services", "backend/app/core", "frontend/src/app", "architecture"),
    ),
    (
        "README.md",
        "feature surface",
        ("frontend/src/features", "frontend/src/components", "frontend/src/pages"),
    ),
    (
        "docs/SPRINT_ROADMAP.md",
        "roadmap status",
        ("roadmap", "milestone", "backlog"),
    ),
]

_COMMENT_ANCHOR = "<!-- waste-iq-agent:doc-proposal v1 -->"
_APPLY_COMMAND = "/agent docs apply"
_BRANCH_PREFIX = "agent/docs-"


class DocUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_path: str
    reason: str
    change_kind: str


class DocProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pr_number: int
    pr_title: str
    changelog_section: str | None = None
    changelog_entry: str | None = None
    doc_updates: list[DocUpdate] = []
    summary: str = ""


def parse_conventional_title(title: str) -> tuple[str, str, str]:
    """Return (type, scope, subject); type/scope may be empty for plain titles."""
    match = _CONVENTIONAL_RE.match(title.strip())
    if not match:
        return "", "", title.strip()
    return match.group(1).lower(), match.group(2) or "", match.group(3).strip()


def changelog_section_for_type(commit_type: str) -> str | None:
    for prefix, section in _CHANGELOG_SECTIONS:
        if commit_type == prefix:
            return section
    return None


def build_changelog_entry(
    pr_number: int, title: str, summary: str | None = None
) -> tuple[str | None, str | None]:
    """Return (section, entry) for a merged PR title, or (None, None).

    The entry is ``**Subject (#<pr>)** — <summary>``; summary falls back to
    the first sentence of the PR body, then to a pointer to the PR itself.
    """
    commit_type, _scope, subject = parse_conventional_title(title)
    section = changelog_section_for_type(commit_type)
    if section is None:
        return None, None
    if summary:
        blurb = summary.split(".")[0].strip()
        if len(blurb) < 10:
            blurb = f"See PR #{pr_number}."
    else:
        blurb = f"See PR #{pr_number}."
    entry = f"- **{subject} (#{pr_number})** — {blurb}."
    return section, entry


class DocAssistant:
    """Deterministic doc proposals for merged PRs."""

    def analyze(
        self,
        pr: dict,
        *,
        changed_files: list[str],
        pr_body: str = "",
    ) -> DocProposal:
        number = int(pr.get("number") or 0)
        title = pr.get("title") or ""
        section, entry = build_changelog_entry(number, title, pr_body)
        proposal = DocProposal(
            pr_number=number,
            pr_title=title,
            changelog_section=section,
            changelog_entry=entry,
            doc_updates=self._detect_drift(changed_files),
        )
        proposal.summary = self._summarize(proposal)
        return proposal

    # ------------------------------------------------------------------
    def _detect_drift(self, changed_files: list[str]) -> list[DocUpdate]:
        updates: list[DocUpdate] = []
        for doc_path, change_kind, markers in DOC_DRIFT_RULES:
            touched = [path for path in changed_files if any(m in path for m in markers)]
            if not touched:
                continue
            updates.append(
                DocUpdate(
                    doc_path=doc_path,
                    reason=f"PR touches {', '.join(sorted(touched)[:3])}",
                    change_kind=change_kind,
                )
            )
        return updates

    def _summarize(self, proposal: DocProposal) -> str:
        parts = []
        if proposal.changelog_entry:
            parts.append(f"changelog entry under '{proposal.changelog_section}'")
        if proposal.doc_updates:
            parts.append(f"{len(proposal.doc_updates)} doc update suggestion(s)")
        if not parts:
            parts.append("no concrete doc changes suggested")
        return f"Proposal for PR #{proposal.pr_number}: {', '.join(parts)}."


def format_proposal_comment(proposal: DocProposal) -> str:
    """Propose-only comment body with an idempotency anchor."""
    lines = [
        _COMMENT_ANCHOR,
        "### AI Agent docs proposal (propose-only)",
        "",
        proposal.summary,
    ]
    if proposal.changelog_entry:
        lines += [
            "",
            f"**Changelog** (under `### {proposal.changelog_section}` in `CHANGELOG.md`):",
            "",
            "```markdown",
            proposal.changelog_entry,
            "```",
        ]
    if proposal.doc_updates:
        lines += ["", "**Suggested doc updates (manual review):**"]
        for update in proposal.doc_updates:
            lines.append(f"- `{update.doc_path}` — {update.reason}")
    lines += [
        "",
        f"Reply `{_APPLY_COMMAND}` to open a patch PR with the changelog entry "
        "(doc-update suggestions are listed in the PR description for manual follow-up).",
        "",
        "_Automated proposal only — nothing was modified in this repository._",
    ]
    return "\n".join(lines)


def patch_branch_name(pr_number: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{_BRANCH_PREFIX}{pr_number}-{stamp}"


def apply_changelog_insertion(changelog: str, section: str, entry: str) -> tuple[str, bool]:
    """Insert ``entry`` under ``### {section}`` in ``## [Unreleased]``.

    Returns (new content, inserted). If the section is missing under
    [Unreleased], it is created in the canonical Keep-a-Changelog order.
    """
    lines = changelog.splitlines()
    unreleased_index: int | None = None
    section_index: int | None = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## "):
            if line.strip().lower() == "## [unreleased]":
                unreleased_index = i
            elif unreleased_index is not None and section_index is None:
                break
        elif unreleased_index is not None and line.strip() == f"### {section}":
            section_index = i
    if unreleased_index is None:
        return changelog, False
    if section_index is None:
        return _insert_new_section(lines, unreleased_index, section, entry)
    insert_at = _section_end(lines, section_index)
    lines.insert(insert_at, entry)
    return "\n".join(lines) + "\n", True


def _section_end(lines: list[str], section_index: int) -> int:
    i = section_index + 1
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("### ") or stripped.startswith("## "):
            break
        i += 1
    return i


def _insert_new_section(
    lines: list[str], unreleased_index: int, section: str, entry: str
) -> tuple[str, bool]:
    existing: set[str] = set()
    i = unreleased_index + 1
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("## ") and not stripped.lower() == "## [unreleased]":
            break
        if stripped.startswith("### "):
            existing.add(stripped[4:].strip())
        i += 1
    ordered = [s for s in _SECTION_ORDER if s in existing]
    insert_before: int | None = None
    for candidate in ordered:
        if candidate > section:
            idx = _find_section_header(lines, candidate, unreleased_index)
            if idx is not None:
                insert_before = idx
            break
    block = ["", f"### {section}", entry]
    if insert_before is None:
        insert_before = i
        if insert_before < len(lines) and lines[insert_before].strip().startswith("## "):
            block.append("")
    lines[insert_before:insert_before] = block
    return "\n".join(lines) + "\n", True


def _find_section_header(lines: list[str], section: str, start: int) -> int | None:
    for i in range(start, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("## ") and not stripped.lower() == "## [unreleased]":
            return None
        if stripped == f"### {section}":
            return i
    return None
