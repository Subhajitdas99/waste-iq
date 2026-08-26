"""Forgot & reset password lifecycle (WIQ-V1-015).

Design notes
------------
- Reset tokens are signed, expiring JWTs carrying ``purpose="password_reset"``
  and a fingerprint of the user's current password hash (see
  :mod:`app.core.security`). Nothing is stored server-side; single-use
  semantics come from the state transition the token performs: once the
  password hash changes, the embedded fingerprint no longer matches and the
  token — along with any other outstanding reset token — is dead.
- Every invalid, expired, malformed, or stale token surfaces as the same
  generic :class:`PasswordResetError` so responses never reveal anything
  about accounts or tokens.
- Audit events record only identifiers and outcomes — never token material,
  passwords, or hashes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.security import (
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    password_fingerprint,
    verify_password,
)
from app.db.session import SessionLocal
from app.models.user import User
from app.services.audit import AuditService
from app.services.email import EmailDeliveryError, send_password_reset_email as deliver_email
from app.services.refresh_token import RefreshTokenService

logger = logging.getLogger(__name__)

_audit_service = AuditService()
_refresh_token_service = RefreshTokenService()

# Generic detail shared by every reset failure so clients cannot distinguish
# invalid, expired, malformed, reused, or stale tokens.
INVALID_RESET_TOKEN_DETAIL = "Invalid or expired reset token"

# Session factory used by the background delivery task. Overridable in tests so
# the task writes to the same database as the request that scheduled it.
delivery_session_factory: Callable[[], Session] = SessionLocal


class PasswordResetError(ValueError):
    """Raised for invalid, expired, or otherwise unusable reset tokens."""


def complete_password_reset_email_delivery(user_id: int) -> None:
    """Deliver the password-reset email off the request path (WIQ-V1-021).

    Executed as a FastAPI ``BackgroundTask`` after ``forgot-password`` has
    responded, so SMTP I/O never blocks the API response. Owns a fresh
    database session because the request-scoped session is closed by the time
    the task runs. Never raises: delivery failures are logged so the request
    outcome is unaffected. The ``password_reset_email_sent`` audit event is
    recorded only after the provider accepts the message. Never logs token
    material.
    """
    db = delivery_session_factory()
    try:
        user = db.get(User, user_id)
        if user is None:
            logger.warning(
                "Password reset email skipped: user %s no longer exists",
                user_id,
            )
            return

        token = create_password_reset_token(str(user.id), password_fingerprint(user.password_hash))

        try:
            deliver_email(user, token)
        except EmailDeliveryError:
            logger.error(
                "Password reset email delivery failed for user %s",
                user_id,
                exc_info=True,
            )
            return

        _audit_service.record(
            db,
            actor_user_id=user_id,
            action="password_reset_email_sent",
            resource="user",
            resource_id=str(user_id),
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Background password reset email delivery failed for user %s", user_id)
    finally:
        db.close()


def reset_password(db: Session, token: str, new_password: str) -> User:
    """Validate ``token`` and set a new password, revoking every session.

    Raises :class:`PasswordResetError` for any unusable token and
    :class:`ValueError` when the new password violates policy (e.g. it equals
    the current password). On success the password hash is replaced, every
    refresh session of the user is revoked, and a ``password_reset`` audit
    event is recorded in the same transaction.
    """
    try:
        subject, fingerprint = decode_password_reset_token(token)
    except ValueError as exc:
        raise PasswordResetError(INVALID_RESET_TOKEN_DETAIL) from exc

    try:
        user_id = int(subject)
    except ValueError:
        raise PasswordResetError(INVALID_RESET_TOKEN_DETAIL) from None

    user = db.get(User, user_id)
    if user is None:
        # Signed token referencing a deleted account: same generic response.
        raise PasswordResetError(INVALID_RESET_TOKEN_DETAIL)

    # Single-use enforcement: the token embeds a fingerprint of the password
    # hash as it was when the token was issued. Any password change since then
    # (including an earlier completed reset with this very token) invalidates
    # it — without any server-side token store or migration.
    if fingerprint != password_fingerprint(user.password_hash):
        raise PasswordResetError(INVALID_RESET_TOKEN_DETAIL)

    if verify_password(new_password, user.password_hash):
        # Same policy as change-password: the new password must differ.
        raise ValueError("New password must be different from the current password")

    user.password_hash = hash_password(new_password)
    # Unlike change-password there is no "current session" to keep: a reset
    # proves nothing about which device holds which session, so all of them go.
    _refresh_token_service.revoke_all_for_user(db, user.id)
    _audit_service.record(
        db,
        actor_user_id=user.id,
        action="password_reset",
        resource="user",
        resource_id=str(user.id),
    )
    db.commit()
    db.refresh(user)
    return user
