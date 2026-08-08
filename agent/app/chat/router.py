"""Developer Chat Assistant HTTP API (Phase 5).

POST /api/chat             — answer a question
POST /api/chat/followup    — answer a follow-up against an existing conversation
GET  /api/chat/status      — conversation status, provider, memory, cache
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import get_chat_service
from app.api.routes.llm import _consider as _consider_llm
from app.chat.models import (
    ChatNoEvidenceError,
    ChatNotFoundError,
    ChatRequest,
    ChatResponse,
    ChatStatus,
    ChatValidationError,
    FollowUpRequest,
)
from app.chat.service import ChatService
from app.llm.models import LLMError
from app.review.review_models import ReviewUnavailable

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _consider(exc: Exception) -> HTTPException:
    """Map chat-layer and upstream errors to HTTP responses."""
    if isinstance(exc, ChatValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, ChatNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ChatNoEvidenceError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, ReviewUnavailable):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, LLMError):
        return _consider_llm(exc)
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post(
    "",
    response_model=ChatResponse,
    summary="Answer a repository question with grounded evidence",
)
def chat(
    request: ChatRequest,
    x_request_id: str | None = Header(default=None),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Detect intent, retrieve evidence, dispatch the right agent, ground the answer."""
    try:
        return chat_service.answer(request, correlation_id=x_request_id)
    except Exception as exc:  # noqa: BLE001 - mapped by _consider
        raise _consider(exc) from exc


@router.post(
    "/followup",
    response_model=ChatResponse,
    summary="Answer a follow-up question using conversation context",
)
def chat_followup(
    request: FollowUpRequest,
    x_request_id: str | None = Header(default=None),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Resolve the follow-up against the previous conversation's context."""
    try:
        return chat_service.followup(request, correlation_id=x_request_id)
    except Exception as exc:  # noqa: BLE001 - mapped by _consider
        raise _consider(exc) from exc


@router.get(
    "/status",
    response_model=ChatStatus,
    summary="Chat conversation status, provider and memory usage",
)
def chat_status(
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatStatus:
    return chat_service.status()
