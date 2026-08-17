"""Subword tokenizer for code-aware retrieval.

Splits identifiers written in snake_case and camelCase into their
constituent words so that queries like "refresh token", "refresh_token"
or "refreshToken" all match code such as ``refreshAccessToken()`` or
``REFRESH_TOKEN_STORAGE_KEY``.
"""

from __future__ import annotations

import re

_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")

_MIN_LEN = 2


def split_identifier(identifier: str) -> list[str]:
    """Split one identifier into lowercase words ("ReviewEngine" -> [review, engine])."""
    parts = [part for part in identifier.split("_") if part]
    words: list[str] = []
    for part in parts:
        words.extend(_CAMEL_RE.findall(part))
    return [word.lower() for word in words if len(word) >= _MIN_LEN]


def subword_tokens(text: str) -> list[str]:
    """All subword tokens in ``text``, preserving repetition."""
    tokens: list[str] = []
    for match in _WORD_RE.findall(text):
        tokens.extend(split_identifier(match))
    return tokens


def unique_subword_tokens(text: str) -> list[str]:
    """Deduplicated subword tokens, in first-seen order."""
    seen: set[str] = set()
    unique: list[str] = []
    for token in subword_tokens(text):
        if token not in seen:
            seen.add(token)
            unique.append(token)
    return unique


def singularize(token: str) -> str:
    """Strip a trailing plural 's' ("notifications" -> "notification").

    Conservative: skips tokens that already end in double-'s' or '-is'
    ("class", "status"), and tokens too short to be safe.
    """
    if (
        len(token) >= 4
        and token.endswith("s")
        and not token.endswith("ss")
        and not token.endswith("is")
        and not token.endswith("us")
    ):
        return token[:-1]
    return token


def expand_query_tokens(text: str) -> list[str]:
    """Query tokens plus singular variants, deduplicated in first-seen order.

    Query-side recall expansion only: a plural query ("notifications")
    also matches content that uses the singular form ("notification").
    The reverse direction (singular query -> plural content) is not
    expanded, because added plural tokens can pull in unrelated dense
    files ("token" -> "tokens") and regress precision.
    """
    expanded: list[str] = []
    for token in unique_subword_tokens(text):
        if token not in expanded:
            expanded.append(token)
        alt = singularize(token)
        if alt != token and alt not in expanded:
            expanded.append(alt)
    return expanded


def whole_identifier_tokens(text: str) -> list[str]:
    """Raw identifier tokens (no camel/snake splitting), lowercased."""
    return [m.lower() for m in _WORD_RE.findall(text) if len(m) >= _MIN_LEN]


_STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "are",
    "not",
    "from",
    "def",
    "class",
    "import",
    "return",
    "if",
    "else",
    "is",
    "in",
    "to",
}


def make_keywords(text: str, limit: int = 12) -> list[str]:
    """Top-TF subword tokens for a text (metadata/debug use)."""
    from collections import Counter

    counts = Counter(t for t in subword_tokens(text) if len(t) >= 3 and t not in _STOP_WORDS)
    return [token for token, _ in counts.most_common(limit)]
