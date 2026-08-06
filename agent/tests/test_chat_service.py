"""Unit tests for ChatService — sanitization, memory, status (Phase 5)."""

import pytest

from app.chat.models import (
    ChatNotFoundError,
    ChatRequest,
    ChatValidationError,
    FollowUpRequest,
)
from app.chat.orchestrator import ChatOutcome
from app.chat.service import ChatService
from app.llm.service import LLMService


class _FakeOrchestrator:
    def __init__(self) -> None:
        self.calls = 0
        self.last_previous_turns = None

    def handle(self, question, *, correlation_id=None, previous_turns=None):
        self.calls += 1
        self.last_previous_turns = previous_turns
        return ChatOutcome(
            intent="explain_code",
            answer=f"answer for {question}",
            confidence=0.8,
            references=[],
            provider="fake",
            grounded=False,
            search_query="login",
        )


@pytest.fixture
def service():
    orchestrator = _FakeOrchestrator()
    chat_service = ChatService(llm_service=LLMService(), orchestrator=orchestrator)
    return chat_service, orchestrator


def test_answer_creates_conversation_and_records_turn(service):
    chat_service, orchestrator = service
    response = chat_service.answer(ChatRequest(question="Explain the login route"))
    assert response.conversation_id is not None
    assert response.answer == "answer for Explain the login route"
    assert response.provider == "fake"
    assert orchestrator.calls == 1
    assert chat_service._memory.memory_turns == 1  # noqa: SLF001


def test_answer_reuses_given_conversation_id(service):
    chat_service, _ = service
    response = chat_service.answer(
        ChatRequest(question="Explain the login route", conversation_id="my-conv")
    )
    assert response.conversation_id == "my-conv"
    assert chat_service._memory.get("my-conv") is not None  # noqa: SLF001


def test_answer_passes_recent_turns_as_context(service):
    chat_service, orchestrator = service
    first = chat_service.answer(ChatRequest(question="Question one"))
    chat_service.answer(ChatRequest(question="Question two", conversation_id=first.conversation_id))
    assert orchestrator.last_previous_turns is not None
    assert len(orchestrator.last_previous_turns) == 1
    assert orchestrator.last_previous_turns[-1].question == "Question one"


def test_followup_uses_existing_conversation(service):
    chat_service, _ = service
    first = chat_service.answer(ChatRequest(question="Question one"))
    second = chat_service.followup(
        FollowUpRequest(question="what about it?", conversation_id=first.conversation_id)
    )
    assert second.conversation_id == first.conversation_id
    assert chat_service._memory.memory_turns == 2  # noqa: SLF001


def test_followup_unknown_conversation_raises(service):
    chat_service, _ = service
    with pytest.raises(ChatNotFoundError):
        chat_service.followup(FollowUpRequest(question="what about it?", conversation_id="missing"))


def test_oversized_question_rejected():
    chat_service = ChatService(llm_service=LLMService(), orchestrator=_FakeOrchestrator())
    with pytest.raises(ChatValidationError):
        chat_service._sanitize("x" * 5000)  # noqa: SLF001


def test_secret_shaped_question_rejected():
    chat_service = ChatService(llm_service=LLMService(), orchestrator=_FakeOrchestrator())
    with pytest.raises(ChatValidationError):
        chat_service._sanitize(  # noqa: SLF001
            "What is the api_key=sk-abcdefghijklmnopqrstuvwxyz123456 for?"
        )
    with pytest.raises(ChatValidationError):
        chat_service._sanitize(  # noqa: SLF001
            "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc.def token leak"
        )


def test_sanitize_strips_whitespace():
    chat_service = ChatService(llm_service=LLMService(), orchestrator=_FakeOrchestrator())
    assert chat_service._sanitize("  hello world  ") == "hello world"  # noqa: SLF001


def test_status_reports_provider_and_memory():
    chat_service = ChatService(llm_service=LLMService(), orchestrator=_FakeOrchestrator())
    chat_service.answer(ChatRequest(question="Where is the service?"))
    status = chat_service.status()
    assert status.provider == "mock"
    assert status.configured is True
    assert status.cache_backend == "memory"
    assert status.conversations == 1
    assert status.memory_turns == 1
    assert status.max_turns == 10
    assert status.intent_counts["explain_code"] == 1
    assert status.intent_counts["unknown"] == 0


def test_status_respects_custom_max_turns():
    from app.chat.memory import MemoryStore

    chat_service = ChatService(
        llm_service=LLMService(), orchestrator=_FakeOrchestrator(), memory=MemoryStore(max_turns=3)
    )
    assert chat_service.status().max_turns == 3


def test_memory_bounds_conversation_length(service):
    chat_service, _ = service
    conversation_id = None
    for i in range(15):
        response = chat_service.answer(
            ChatRequest(question=f"Question {i}", conversation_id=conversation_id)
        )
        conversation_id = response.conversation_id
    conversation = chat_service._memory.get(conversation_id)  # noqa: SLF001
    assert conversation is not None
    assert len(conversation.turns) <= 10


def test_extra_attributes_rejected():
    with pytest.raises(Exception):
        ChatRequest(question="hi", unknown_field=True)  # type: ignore[call-arg]
