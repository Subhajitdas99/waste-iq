"""In-process conversation memory for the Developer Chat Assistant.

Thread-safe keyed store of bounded conversations. No persistence, no vector
embeddings, no re-indexing — a follow-up only needs the last few turns.
"""

from __future__ import annotations

import threading
import uuid

from app.chat.conversation import Conversation, ConversationTurn, _MAX_TURNS_DEFAULT


class MemoryStore:
    """Bounded, thread-safe conversation storage keyed by conversation id."""

    def __init__(self, max_turns: int = _MAX_TURNS_DEFAULT) -> None:
        self._max_turns = max_turns
        self._conversations: dict[str, Conversation] = {}
        self._lock = threading.RLock()

    @property
    def max_turns(self) -> int:
        return self._max_turns

    def create_conversation(self) -> str:
        conversation_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._conversations[conversation_id] = Conversation(conversation_id, self._max_turns)
        return conversation_id

    def get(self, conversation_id: str) -> Conversation | None:
        with self._lock:
            return self._conversations.get(conversation_id)

    def ensure(self, conversation_id: str) -> Conversation:
        with self._lock:
            return self._conversations.setdefault(
                conversation_id, Conversation(conversation_id, self._max_turns)
            )

    def append(self, conversation_id: str, turn: ConversationTurn) -> Conversation:
        with self._lock:
            conversation = self._conversations.setdefault(
                conversation_id, Conversation(conversation_id, self._max_turns)
            )
            conversation.append(turn)
            return conversation

    def clear(self) -> None:
        with self._lock:
            self._conversations.clear()

    @property
    def conversations(self) -> int:
        with self._lock:
            return len(self._conversations)

    @property
    def memory_turns(self) -> int:
        with self._lock:
            return sum(len(conversation.turns) for conversation in self._conversations.values())
