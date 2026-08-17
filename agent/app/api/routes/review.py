from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.api.dependencies import get_review_service
from app.review.review_models import PRReview, ReviewRequest, ReviewStatus, ReviewUnavailable
from app.review.review_service import ReviewService

router = APIRouter(tags=["review"])


@router.post(
    "/api/review/pr",
    response_model=PRReview,
    summary="Review a pull request",
)
def review_pr(
    request: ReviewRequest,
    review_service: ReviewService = Depends(get_review_service),
    x_request_id: str | None = Header(default=None),
) -> PRReview:
    """Analyze a PR (metadata + diff) against repository context.

    Returns a structured review object. The agent never posts comments,
    merges, or modifies code.
    """
    try:
        return review_service.submit(request, correlation_id=x_request_id)
    except ReviewUnavailable as exc:
        detail = str(exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        ) from exc


@router.get("/api/review/status", response_model=ReviewStatus)
def review_status(
    review_service: ReviewService = Depends(get_review_service),
) -> ReviewStatus:
    """Health, queue size, pending reviews and statistics."""
    return review_service.status()


@router.get("/api/review/sessions")
def review_sessions(
    limit: int = Query(default=10, ge=1, le=100),
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    return {"sessions": review_service.recent(limit)}


@router.get("/api/review/sessions/{session_id}")
def review_session(
    session_id: int,
    review_service: ReviewService = Depends(get_review_service),
) -> dict:
    session = review_service.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return session
