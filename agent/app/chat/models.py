"""Typed models for the Developer Chat Assistant (Phase 5).

The chat layer is a thin orchestration facade: it never re-implements
retrieval, review, triage, or documentation logic. Every model here is the
conversational envelope around the existing services.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

IntentName = Literal[
    "explain_architecture",
    "explain_code",
    "find_implementation",
    "review_pr",
    "generate_issue",
    "summarize_changes",
    "generate_documentation",
    "repository_search",
    "unknown",
]

INTENT_NAMES: tuple[IntentName, ...] = (
    "explain_architecture",
    "explain_code",
    "find_implementation",
    "review_pr",
    "generate_issue",
    "summarize_changes",
    "generate_documentation",
    "repository_search",
    "unknown",
)


class ChatRequest(BaseModel):
    """A single chat question. Conversation id is optional (memory starts fresh)."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=64)


class FollowUpRequest(BaseModel):
    """A follow-up question tied to an existing conversation."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str = Field(min_length=1, max_length=64)


class ChatReference(BaseModel):
    """One repository-grounded citation for a chat answer."""

    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    chunk_id: str | None = None
    evidence_id: str | None = None
    source_type: str = "code"


class ChatResponse(BaseModel):
    """The conversational answer with its repository evidence."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentName
    answer: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    references: list[ChatReference] = Field(default_factory=list)
    provider: str = ""
    model: str = ""
    cached: bool = False
    latency_ms: int = 0
    conversation_id: str | None = None
    correlation_id: str | None = None
    grounded: bool = False
    notes: list[str] = Field(default_factory=list)


class ChatStatus(BaseModel):
    """Conversation status: provider, memory, cache, intent statistics."""

    enabled: bool
    provider: str
    configured: bool
    model: str
    cache_backend: str
    cache_hits: int
    conversations: int
    memory_turns: int
    max_turns: int
    intent_counts: dict[IntentName, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Errors


class ChatError(Exception):
    """Base class for Developer Chat Assistant errors."""


class ChatValidationError(ChatError):
    """The question is rejected (too large or contains sensitive content)."""


class ChatNoEvidenceError(ChatError):
    """The question could not be answered with repository evidence."""


class ChatNotFoundError(ChatError):
    """The requested conversation does not exist."""
