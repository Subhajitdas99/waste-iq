"""Deterministic intent detection for the Developer Chat Assistant.

Intent detection is keyword/pattern based by design — no LLM classification.
Rules are ordered most-specific first; the first rule with a keyword match
wins. Confidence is a deterministic function of the number of matched
keywords (capped), so identical questions always produce identical intents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.chat.models import IntentName

_WORD_RE = re.compile(r"[a-z0-9_]+")


@dataclass(frozen=True)
class IntentResult:
    """The deterministic classification of one question."""

    intent: IntentName
    confidence: float
    subject: str
    matched_keywords: tuple[str, ...]


# (intent, keywords, base_confidence)
_INTENT_RULES: list[tuple[IntentName, tuple[str, ...], float]] = [
    (
        "review_pr",
        (
            "review this pr",
            "review the pr",
            "review pr",
            "review pull request",
            "review the pull request",
            "review this pull request",
            "review #",
            "pr review",
            "pull request review",
        ),
        0.92,
    ),
    (
        "generate_issue",
        (
            "generate issue",
            "generate an issue",
            "create issue",
            "create an issue",
            "write issue",
            "issue draft",
            "triage issue",
            "generate an issue draft",
            "issue triage",
        ),
        0.92,
    ),
    (
        "generate_documentation",
        (
            "generate documentation",
            "write documentation",
            "create documentation",
            "documentation for",
            "document this",
            "update documentation",
            "generate changelog",
            "changelog entry",
            "api documentation",
            "write docs",
            "update docs",
        ),
        0.9,
    ),
    (
        "summarize_changes",
        (
            "summarize",
            "summarise",
            "summary of",
            "what changed",
            "summarize the changes",
            "summarize changes",
            "summarize pr",
            "summarize this pr",
        ),
        0.9,
    ),
    (
        "explain_architecture",
        (
            "architecture",
            "workflow",
            "adr",
            "design decision",
            "end to end flow",
            "end-to-end flow",
            "system design",
            "how does it fit together",
        ),
        0.88,
    ),
    (
        "find_implementation",
        (
            "where is",
            "where are",
            "where's",
            "where can i find",
            "find implementation",
            "which file",
            "which module",
            "in which file",
            "where is it implemented",
            "find the implementation",
            "locate",
        ),
        0.86,
    ),
    (
        "explain_code",
        (
            "explain",
            "how does",
            "how do",
            "how is",
            "what does",
            "what do",
            "what is",
            "what are",
            "why does",
            "why is",
            "what's",
            "tell me about",
            "describe",
        ),
        0.82,
    ),
    (
        "repository_search",
        (
            "search for",
            "search the repository",
            "search the repo",
            "repository search",
            "search repo",
            "search",
        ),
        0.78,
    ),
]

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "how",
        "what",
        "why",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "does",
        "do",
        "did",
        "can",
        "could",
        "would",
        "should",
        "will",
        "please",
        "you",
        "your",
        "me",
        "my",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "there",
        "here",
        "with",
        "for",
        "of",
        "on",
        "in",
        "to",
        "from",
        "about",
        "and",
        "or",
        "not",
        "no",
        "the",
        "explain",
        "generate",
        "create",
        "write",
        "review",
        "find",
        "search",
        "summarize",
        "summarise",
        "describe",
        "show",
        "tell",
        "give",
        "need",
        "want",
        "help",
        "know",
        "understand",
        "implement",
        "implemented",
    }
)


def _normalize(question: str) -> str:
    return re.sub(r"[^a-z0-9_ ]+", " ", question.lower())


def _subject(question: str, matched: tuple[str, ...]) -> str:
    """Strip intent keywords and stopwords; keep the meaningful target words."""
    matched_words = {word for phrase in matched for word in _WORD_RE.findall(phrase)}
    tokens = _WORD_RE.findall(_normalize(question))
    seen: list[str] = []
    for token in tokens:
        if token in _STOPWORDS or token in matched_words:
            continue
        if token not in seen:
            seen.append(token)
    return " ".join(seen[:8])


def detect_intent(question: str) -> IntentResult:
    """Classify a question into one of the supported intents (deterministic)."""
    normalized = _normalize(question)
    for intent, keywords, base in _INTENT_RULES:
        matched = tuple(keyword for keyword in keywords if keyword in normalized)
        if matched:
            confidence = min(0.99, base + 0.02 * min(len(matched), 4))
            return IntentResult(
                intent=intent,
                confidence=round(confidence, 2),
                subject=_subject(question, matched),
                matched_keywords=matched,
            )
    return IntentResult(intent="unknown", confidence=0.1, subject="", matched_keywords=())
