"""Conversation state — lightweight, in-memory, max 10 turns (Phase 5).

Memory keeps only what the next follow-up needs: the recent questions, the
retrieved references, and the search query that produced them. There is no
vector memory and no repository re-indexing.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.chat.models import ChatReference, IntentName

_MAX_TURNS_DEFAULT = 10


class ConversationTurn(BaseModel):
    """One recorded question/answer pair inside a conversation."""

    model_config = ConfigDict(extra="forbid")

    question: str
    intent: IntentName
    answer: str
    references: list[ChatReference] = Field(default_factory=list)
    search_query: str = ""
    cached: bool = False
    latency_ms: int = 0


class Conversation:
    """An ordered list of turns with a bounded capacity."""

    def __init__(self, conversation_id: str, max_turns: int = _MAX_TURNS_DEFAULT) -> None:
        self.conversation_id = conversation_id
        self.max_turns = max_turns
        self.turns: list[ConversationTurn] = []

    def append(self, turn: ConversationTurn) -> int:
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]
        return len(self.turns)

    @property
    def recent_questions(self) -> list[str]:
        return [turn.question for turn in self.turns[-3:]]

    @property
    def last_turn(self) -> ConversationTurn | None:
        return self.turns[-1] if self.turns else None

    @property
    def references(self) -> list[ChatReference]:
        """All references cited across the retained turns (deduplicated)."""
        seen: dict[tuple[str, int | None, int | None], ChatReference] = {}
        for turn in self.turns:
            for ref in turn.references:
                seen.setdefault((ref.file_path, ref.start_line, ref.end_line), ref)
        return list(seen.values())


def resolve_query(
    question: str,
    subject: str,
    previous_turn: ConversationTurn | None,
) -> tuple[str, bool]:
    """Pick the search query for a question, following up when needed.

    Returns (query, used_followup): when the question carries no subject of
    its own (e.g. "what about it?"), the previous turn's search query is
    reused so the follow-up resolves against the same repository evidence.
    """
    if subject:
        return subject, False
    if previous_turn and previous_turn.search_query:
        return previous_turn.search_query, True
    return question.strip(), False
