"""FastAPI dependency providers."""

from __future__ import annotations

from app.chat.service import ChatService
from app.context.context_service import ContextService
from app.context.di import Container
from app.db.session import SessionLocal
from app.llm.service import LLMService
from app.review.review_service import ReviewService

_container: Container | None = None
_review_service: ReviewService | None = None
_llm_service: LLMService | None = None
_chat_service: ChatService | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container(SessionLocal)
    return _container


def get_context_service() -> ContextService:
    return ContextService(get_container())


def get_review_service() -> ReviewService:
    global _review_service
    if _review_service is None:
        _review_service = ReviewService(container=get_container())
    return _review_service


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(container=get_container(), llm_service=get_llm_service())
    return _chat_service
