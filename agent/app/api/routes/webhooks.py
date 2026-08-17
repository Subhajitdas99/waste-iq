import json
import logging

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import verify_webhook_signature
from app.coordinator.event_handler import parse_event
from app.coordinator.orchestrator import EventOrchestrator
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])


@router.post("/api/webhooks/github")
async def github_webhook(request: Request) -> Response:
    signature = request.headers.get("x-hub-signature-256")
    body = await request.body()

    if not verify_webhook_signature(body, signature, settings.agent_webhook_secret):
        return JSONResponse(
            {"detail": "invalid signature"}, status_code=status.HTTP_401_UNAUTHORIZED
        )

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JSONResponse(
            {"detail": "invalid JSON body"}, status_code=status.HTTP_400_BAD_REQUEST
        )

    envelope = parse_event(payload, dict(request.headers))
    if envelope is None:
        return JSONResponse({"detail": "malformed event"}, status_code=status.HTTP_400_BAD_REQUEST)

    db = SessionLocal()
    try:
        EventOrchestrator(db).process(envelope)
    finally:
        db.close()

    review_triggered: dict[str, object] | None = None
    if settings.agent_review_enabled and settings.agent_review_auto_run:
        try:
            from app.review.review_service import ReviewService

            review = ReviewService().review_event(envelope)
            if review is not None:
                review_triggered = {
                    "session_id": review.session_id,
                    "findings_count": len(review.findings),
                }
        except Exception:  # noqa: BLE001 - a review failure must not fail the webhook ack
            logger.exception("review dispatch failed delivery=%s", envelope.delivery_id)

    issue_triggered: dict[str, object] | None = None
    if settings.agent_issue_enabled and settings.agent_issue_auto_run:
        try:
            from app.agents.issue_service import IssueService

            issue_triggered = await IssueService().handle_event(envelope)
        except Exception:  # noqa: BLE001 - a triage failure must not fail the webhook ack
            logger.exception("issue dispatch failed delivery=%s", envelope.delivery_id)

    docs_triggered: dict[str, object] | None = None
    if settings.agent_docs_enabled and (
        settings.agent_docs_auto_run or settings.agent_docs_patch_pr_enabled
    ):
        try:
            from app.agents.doc_service import DocService

            docs_triggered = await DocService().handle_event(envelope)
        except Exception:  # noqa: BLE001 - a docs failure must not fail the webhook ack
            logger.exception("docs dispatch failed delivery=%s", envelope.delivery_id)

    response_body: dict[str, object] = {"delivery_id": envelope.delivery_id, "status": "accepted"}
    if review_triggered is not None:
        response_body["review"] = review_triggered
    if issue_triggered is not None:
        response_body["issue"] = issue_triggered
    if docs_triggered is not None:
        response_body["docs"] = docs_triggered
    return JSONResponse(response_body, status_code=status.HTTP_202_ACCEPTED)
