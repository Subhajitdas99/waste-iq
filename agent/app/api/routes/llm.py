from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import get_llm_service
from app.llm.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExplainRequest,
    ExplainResponse,
    GroundingViolationError,
    LLMError,
    LLMNotConfigured,
    LLMProviderError,
    LLMStatus,
    LLMTimeoutError,
    MalformedResponseError,
    ProviderInfo,
    RateLimitedError,
    SummarizeRequest,
    SummarizeResponse,
)
from app.llm.service import LLMService

router = APIRouter(tags=["llm"])


def _consider(exc: LLMError) -> HTTPException:
    """Map an LLM-layer error to an HTTP response."""
    if isinstance(exc, LLMNotConfigured):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, RateLimitedError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    if isinstance(exc, LLMTimeoutError):
        return HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc))
    if isinstance(exc, (LLMProviderError, MalformedResponseError)):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    if isinstance(exc, GroundingViolationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post(
    "/api/llm/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze review findings with the grounded LLM layer",
)
def llm_analyze(
    request: AnalyzeRequest,
    x_request_id: str | None = Header(default=None),
    llm_service: LLMService = Depends(get_llm_service),
) -> AnalyzeResponse:
    """Reason over supplied findings + context; every reference is grounded."""
    try:
        return llm_service.analyze(request, correlation_id=x_request_id)
    except LLMError as exc:
        raise _consider(exc) from exc


@router.post(
    "/api/llm/explain",
    response_model=ExplainResponse,
    summary="Explain repository behavior grounded in retrieved evidence",
)
def llm_explain(
    request: ExplainRequest,
    x_request_id: str | None = Header(default=None),
    llm_service: LLMService = Depends(get_llm_service),
) -> ExplainResponse:
    """Answer a question using only the supplied evidence."""
    try:
        return llm_service.explain(request, correlation_id=x_request_id)
    except LLMError as exc:
        raise _consider(exc) from exc


@router.post(
    "/api/llm/summarize",
    response_model=SummarizeResponse,
    summary="Summarize a review grounded in retrieved evidence",
)
def llm_summarize(
    request: SummarizeRequest,
    x_request_id: str | None = Header(default=None),
    llm_service: LLMService = Depends(get_llm_service),
) -> SummarizeResponse:
    """Summarize findings + context into grounded key points."""
    try:
        return llm_service.summarize(request, correlation_id=x_request_id)
    except LLMError as exc:
        raise _consider(exc) from exc


@router.get(
    "/api/llm/providers",
    response_model=list[ProviderInfo],
    summary="List provider availability",
)
def llm_providers(
    llm_service: LLMService = Depends(get_llm_service),
) -> list[ProviderInfo]:
    return llm_service.providers()


@router.get(
    "/api/llm/status",
    response_model=LLMStatus,
    summary="LLM layer health, configuration and telemetry",
)
def llm_status(
    llm_service: LLMService = Depends(get_llm_service),
) -> LLMStatus:
    return llm_service.status()
