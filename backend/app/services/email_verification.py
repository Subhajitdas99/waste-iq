"""Email verification lifecycle (WIQ-V1-014).

Design notes
------------
- Verification tokens are signed, expiring JWTs carrying
  ``purpose="email_verify"`` (see :mod:`app.core.security`). Nothing is
  stored server-side; single-use semantics come from the account state
  transition they perform: once ``email_verified_at`` is set, presenting
  the token again is idempotent and cannot change any state.
- Every invalid, expired, or malformed token surfaces as the same generic
  :class:`EmailVerificationError` so responses never reveal whether an
  account exists.
- Audit events record only identifiers and outcomes — never token material,
  passwords, or hashes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import create_verification_token, decode_verification_token
from app.db.session import SessionLocal
from app.models.user import User
from app.services.audit import AuditService
from app.services.email import EmailDeliveryError, send_verification_email as deliver_email

logger = logging.getLogger(__name__)

_audit_service = AuditService()

# Generic detail shared by every verification failure so clients cannot
# distinguish invalid, expired, malformed, or stale tokens.
INVALID_TOKEN_DETAIL = "Invalid or expired verification token"

# Session factory used by the background delivery task. Overridable in tests so
# the task writes to the same database as the request that scheduled it.
delivery_session_factory: Callable[[], Session] = SessionLocal


class EmailVerificationError(ValueError):
    """Raised for invalid, expired, or otherwise unusable verification tokens."""


def complete_verification_email_delivery(user_id: int) -> None:
    """Deliver the verification email off the request path (WIQ-V1-021).

    Executed as a FastAPI ``BackgroundTask`` after ``register`` /
    ``resend_verification`` have responded, so SMTP I/O never blocks the API
    response. Owns a fresh database session because the request-scoped
    session is closed by the time the task runs. Never raises: delivery
    failures are logged so the request outcome is unaffected. The
    ``verification_email_sent`` audit event is recorded only after the
    provider accepts the message. Never logs token material.
    """
    token = create_verification_token(str(user_id))
    db = delivery_session_factory()
    try:
        user = db.get(User, user_id)
        if user is None:
            logger.warning(
                "Verification email skipped: user %s no longer exists",
                user_id,
            )
            return

        try:
            deliver_email(user, token)
        except EmailDeliveryError:
            logger.error(
                "Verification email delivery failed for user %s",
                user_id,
                exc_info=True,
            )
            return

        _audit_service.record(
            db,
            actor_user_id=user_id,
            action="verification_email_sent",
            resource="user",
            resource_id=str(user_id),
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Background verification email delivery failed for user %s", user_id)
    finally:
        db.close()


def verify_email(db: Session, token: str) -> tuple[str, bool]:
    """Validate ``token`` and mark the account verified.

    Returns ``(message, newly_verified)``; ``newly_verified`` is ``False``
    when the account was already verified (idempotent re-verification).
    Raises :class:`EmailVerificationError` for any unusable token.
    """
    try:
        subject = decode_verification_token(token)
    except ValueError as exc:
        raise EmailVerificationError(INVALID_TOKEN_DETAIL) from exc

    try:
        user_id = int(subject)
    except ValueError:
        raise EmailVerificationError(INVALID_TOKEN_DETAIL) from None

    user = db.get(User, user_id)
    if user is None:
        # Signed token referencing a deleted account: same generic response.
        raise EmailVerificationError(INVALID_TOKEN_DETAIL)

    if user.email_verified:
        return "Email already verified", False

    user.email_verified_at = datetime.now(timezone.utc)
    _audit_service.record(
        db,
        actor_user_id=user.id,
        action="email_verified",
        resource="user",
        resource_id=str(user.id),
        after={"email_verified": True},
    )
    db.commit()
    return "Email verified successfully", True
