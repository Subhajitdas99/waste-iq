"""Deterministic token estimator and chunker for repository files."""

from __future__ import annotations

import hashlib
import re

from app.context.models import Chunk, SourceType

# Rough heuristic: ~4 characters per token for code/text.
_CHARS_PER_TOKEN = 4

_BOUNDARY_START = re.compile(
    r"^(def |class |async def |function |public |private |protected |const " r"|import |export |# )"
)
_BOUNDARY_END = re.compile(r"^$")


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_chunk_id(path: str, start_line: int) -> str:
    return content_hash(f"{path}:{start_line}")[:48]


def _find_boundaries(lines: list[str]) -> list[int]:
    """Indices (line numbers) where a new chunk should start."""
    boundaries: list[int] = []
    for idx, line in enumerate(lines):
        if _BOUNDARY_START.match(line.strip()) or (idx == 0):
            boundaries.append(idx)
    return boundaries


_BOUNDARY_LOOKAHEAD = 6


def _boundary_within(boundaries: set[int], idx: int, lookahead: int) -> bool:
    return any(idx < b <= idx + lookahead for b in boundaries)


def chunk_lines(lines: list[str], min_tokens: int, max_tokens: int) -> list[tuple[int, int]]:
    """Split lines into (start_line, end_line) ranges respecting token limits.

    Prefer breaking on structural boundaries (function/class declarations):
    once the token budget is reached, defer the cut to the next boundary if
    one is close; otherwise hard-split. A tiny trailing chunk (< min_tokens)
    is merged into the previous range.
    """
    if not lines:
        return []

    total_chars = sum(len(line) for line in lines)
    if total_chars // _CHARS_PER_TOKEN <= max_tokens:
        return [(0, len(lines) - 1)]

    boundaries = set(_find_boundaries(lines))
    ranges: list[tuple[int, int]] = []
    current_start = 0
    current_tokens = 0

    for idx, line in enumerate(lines):
        line_tokens = max(1, len(line) // _CHARS_PER_TOKEN)
        if idx in boundaries and idx > current_start and current_tokens >= max_tokens:
            ranges.append((current_start, idx - 1))
            current_start = idx
            current_tokens = line_tokens
            continue
        if current_tokens + line_tokens >= max_tokens and not _boundary_within(
            boundaries, idx, _BOUNDARY_LOOKAHEAD
        ):
            ranges.append((current_start, idx))
            current_start = idx + 1
            current_tokens = 0
            continue
        current_tokens += line_tokens

    if current_start < len(lines):
        trailing_tokens = sum(
            max(1, len(line) // _CHARS_PER_TOKEN) for line in lines[current_start:]
        )
        if trailing_tokens < min_tokens and ranges:
            prev_start, _prev_end = ranges[-1]
            ranges[-1] = (prev_start, len(lines) - 1)
        else:
            ranges.append((current_start, len(lines) - 1))
    return ranges


def chunk_text(
    path: str,
    text: str,
    language: str,
    source_type: SourceType,
    min_tokens: int,
    max_tokens: int,
    section_title: str | None = None,
    base_line: int = 0,
) -> list[Chunk]:
    lines = text.split("\n")
    while lines and not lines[-1]:
        lines.pop()
    ranges = chunk_lines(lines, min_tokens, max_tokens)
    chunks: list[Chunk] = []
    for start, end in ranges:
        content = "\n".join(lines[start : end + 1])
        chunks.append(
            Chunk(
                chunk_id=make_chunk_id(path, start + 1 + base_line),
                file_path=path,
                start_line=start + 1 + base_line,
                end_line=end + 1 + base_line,
                section_title=section_title,
                language=language,
                source_type=source_type,
                content=content,
                content_hash=content_hash(content),
                token_estimate=estimate_tokens(content),
            )
        )
    return chunks
