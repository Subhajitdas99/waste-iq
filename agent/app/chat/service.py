"""ChatService — the conversational facade over intent, planner and memory.

Inputs are sanitized (length + secret-shape redaction check), routed through
the orchestrator, recorded into bounded conversation memory, and surfaced
with intent statistics and LLM-layer status.
"""

from __future__ import annotations

import logging
import time

from app.chat.conversation import ConversationTurn
from app.chat.memory import MemoryStore
from app.chat.models import (
    ChatNotFoundError,
    ChatRequest,
    ChatResponse,
    ChatStatus,
    ChatValidationError,
    FollowUpRequest,
    INTENT_NAMES,
)
from app.chat.orchestrator import ChatOrchestrator
from app.chat.response import build_chat_response
from app.core.config import settings
from app.llm.prompt_builder import Redactor

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates retrieval, agents, grounding and conversation memory."""

    def __init__(
        self,
        container=None,
        llm_service=None,
        *,
        memory: MemoryStore | None = None,
        orchestrator: ChatOrchestrator | None = None,
    ) -> None:
        from app.api.dependencies import get_container, get_llm_service

        self._container = container or get_container()
        self._llm = llm_service or get_llm_service()
        self._memory = memory or MemoryStore(max_turns=settings.agent_chat_max_turns)
        self._orchestrator = orchestrator or ChatOrchestrator(
            self._container, self._llm, limit=settings.agent_chat_retrieval_limit
        )
        self._redactor = Redactor()
        self._intent_counts: dict[str, int] = {}

    # ------------------------------------------------------------------
    def answer(self, request: ChatRequest, *, correlation_id: str | None = None) -> ChatResponse:
        """Answer a question, creating or continuing a conversation."""
        t0 = time.monotonic()
        question = self._sanitize(request.question)
        conversation_id = request.conversation_id or self._memory.create_conversation()
        conversation = self._memory.ensure(conversation_id)

        outcome = self._orchestrator.handle(
            question,
            correlation_id=correlation_id,
            previous_turns=conversation.turns[-2:],
        )

        response = build_chat_response(
            intent=outcome.intent,
            answer=outcome.answer,
            confidence=outcome.confidence,
            references=outcome.references,
            provider=outcome.provider,
            model=outcome.model,
            cached=outcome.cached,
            latency_ms=outcome.latency_ms,
            conversation_id=conversation_id,
            correlation_id=correlation_id,
            grounded=outcome.grounded,
            notes=outcome.notes,
        )
        self._memory.append(
            conversation_id,
            ConversationTurn(
                question=request.question,
                intent=outcome.intent,
                answer=outcome.answer,
                references=outcome.references,
                search_query=outcome.search_query,
                cached=outcome.cached,
                latency_ms=outcome.latency_ms,
            ),
        )
        self._intent_counts[outcome.intent] = self._intent_counts.get(outcome.intent, 0) + 1
        logger.info(
            "chat answered",
            extra={
                "conversation_id": conversation_id,
                "intent": outcome.intent,
                "latency_ms": round((time.monotonic() - t0) * 1000),
                "correlation_id": correlation_id,
            },
        )
        return response

    # ------------------------------------------------------------------
    def followup(
        self, request: FollowUpRequest, *, correlation_id: str | None = None
    ) -> ChatResponse:
        """Answer a follow-up question against an existing conversation."""
        conversation = self._memory.get(request.conversation_id)
        if conversation is None:
            raise ChatNotFoundError(f"unknown conversation '{request.conversation_id}'")
        return self.answer(
            ChatRequest(question=request.question, conversation_id=request.conversation_id),
            correlation_id=correlation_id,
        )

    # ------------------------------------------------------------------
    def status(self) -> ChatStatus:
        """Conversation status: provider, memory, cache, intent statistics."""
        llm_status = self._llm.status()
        counts = {name: self._intent_counts.get(name, 0) for name in INTENT_NAMES}
        return ChatStatus(
            enabled=settings.agent_llm_enabled,
            provider=llm_status.provider,
            configured=llm_status.configured,
            model=llm_status.model,
            cache_backend=llm_status.cache_backend,
            cache_hits=llm_status.cache_hits,
            conversations=self._memory.conversations,
            memory_turns=self._memory.memory_turns,
            max_turns=self._memory.max_turns,
            intent_counts=counts,
        )

    # ------------------------------------------------------------------
    def _sanitize(self, question: str) -> str:
        """Reject oversized or secret-bearing questions before dispatch."""
        if len(question) > settings.agent_chat_max_question_chars:
            raise ChatValidationError("question exceeds the maximum supported length")
        if self._redactor.count(question) > 0:
            raise ChatValidationError("question contains sensitive content")
        return question.strip()
