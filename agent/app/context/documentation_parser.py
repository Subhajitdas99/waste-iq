"""Markdown documentation parser — headings, metadata, and doc chunks."""

from __future__ import annotations

import re

from app.context.code_parser import parse_document
from app.context.models import Chunk

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def split_document_chunks(text: str) -> list[tuple[int, int, str | None]]:
    """Split a markdown document into (start_line, end_line, heading) ranges."""
    lines = text.split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    ranges: list[tuple[int, int, str | None]] = []
    current_start = 0
    current_heading: str | None = None
    for idx, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match:
            if idx > current_start:
                ranges.append((current_start, idx - 1, current_heading))
            current_start = idx
            current_heading = match.group(2).strip()
    if current_start < len(lines):
        ranges.append((current_start, len(lines) - 1, current_heading))
    return ranges


def chunk_document(
    path: str,
    text: str,
    min_tokens: int,
    max_tokens: int,
) -> list[Chunk]:
    """Chunk a document by heading first, then fall back to token limits."""
    metadata = parse_document(path, text)
    from app.context.chunker import chunk_text

    chunks: list[Chunk] = []
    for start, end, heading in split_document_chunks(text):
        section = "\n".join(text.split("\n")[start : end + 1])
        sub_chunks = chunk_text(
            path,
            section,
            language="markdown",
            source_type="docs",
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            section_title=heading or metadata.title,
            base_line=start,
        )
        chunks.extend(sub_chunks)
    if not chunks:
        chunks = chunk_text(
            path,
            text,
            language="markdown",
            source_type="docs",
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            section_title=metadata.title,
        )
    return chunks
