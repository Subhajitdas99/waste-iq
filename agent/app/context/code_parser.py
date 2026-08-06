"""Heuristic code parser — extracts structural elements from source files."""

from __future__ import annotations

import re

from app.context.models import CodeElement, DocumentKind, DocumentMetadata

_IMPORT_RE = re.compile(r"^\s*(import |from \S+ import |#include\s+[<\"])")
_DEF_RE = re.compile(
    r"^\s*(?:async\s+)?(?:def|class|func|function|func\s+\w+|fn\s+\w+"
    r"|public|private|protected|internal|static|const)\b"
)
_DOCSTRING_RE = re.compile(r'"""([^"]*)"""|\'\'\'([^\']*)\'\'\'')
_CLASS_RE = re.compile(r"^\s*class\s+(\w+)")
_FUNC_RE = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(")
_TS_FUNC_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:function|const\s+\w+\s*=\s*"
    r"(?:async\s+)?\(?\w*\)?\s*=>|async\s+function)"
)
_TS_CLASS_RE = re.compile(r"^\s*export\s+class\s+(\w+)")


def _trim_docstring(doc: str) -> str | None:
    doc = doc.strip()
    return doc if doc else None


def parse_code(path: str, text: str, language: str) -> list[CodeElement]:
    elements: list[CodeElement] = []
    lines = text.split("\n")
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if _IMPORT_RE.match(stripped):
            elements.append(CodeElement(kind="import", name=stripped, start_line=idx, end_line=idx))
            continue
        class_match = _CLASS_RE.match(stripped)
        if class_match:
            elements.append(
                CodeElement(kind="class", name=class_match.group(1), start_line=idx, end_line=idx)
            )
            continue
        func_match = _FUNC_RE.match(stripped)
        if func_match:
            elements.append(
                CodeElement(kind="function", name=func_match.group(1), start_line=idx, end_line=idx)
            )
            continue
        if _TS_FUNC_RE.match(stripped) or _DEF_RE.match(stripped) and "function" in stripped:
            elements.append(
                CodeElement(kind="function", name=stripped[:40], start_line=idx, end_line=idx)
            )
    return elements


def parse_docstring_sections(text: str) -> list[str]:
    """Extract top-level markdown headings from a document."""
    headings: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# ") or stripped.startswith("## "):
            headings.append(stripped.lstrip("# ").strip())
    return headings[:20]


def parse_document(path: str, text: str) -> DocumentMetadata:
    """Classify a markdown/plaintext document and extract metadata."""
    lower_path = path.lower()
    kind: DocumentKind = "other"
    if any(seg in lower_path for seg in ("architecture", "arch-", "architecture_decisions")):
        kind = "architecture"
    elif lower_path.endswith("adr") or "/adr/" in lower_path or "adr-" in lower_path:
        kind = "adr"
    elif any(seg in lower_path for seg in ("roadmap", "backlog", "milestone")):
        kind = "roadmap"
    elif "api" in lower_path:
        kind = "api"
    elif "feature" in lower_path or "design" in lower_path:
        kind = "design"
    elif lower_path.endswith(("readme.md", "readme")):
        kind = "readme"
    elif "changelog" in lower_path:
        kind = "changelog"

    sections = parse_docstring_sections(text)
    todos = [
        line.strip()
        for line in text.split("\n")
        if any(tag in line for tag in ("TODO", "TODO:", "FIXME", "XXX"))
    ][:20]
    adr_ids = [m for m in re.findall(r"ADR-?(\d+)", text)][:20]
    milestones = [
        line.strip()
        for line in text.split("\n")
        if re.match(r"^\s*[-*]\s*(?:Milestone|M\d+:)", line)
    ][:20]
    features = [
        line.strip()
        for line in text.split("\n")
        if re.match(r"^\s*[-*]\s*(?:Feature|Enhancement):", line)
    ][:20]
    decisions = [
        line.strip()
        for line in text.split("\n")
        if re.match(r"^\s*[-*]\s*(?:Decision|Status):", line)
    ][:20]

    title = None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break

    return DocumentMetadata(
        path=path,
        kind=kind,
        title=title,
        sections=sections,
        todos=todos,
        milestones=milestones,
        adr_ids=adr_ids,
        features=features,
        decisions=decisions,
    )
