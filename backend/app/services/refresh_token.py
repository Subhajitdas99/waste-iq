"""Server-side refresh-token sessions with rotation and reuse detection.

WIQ-V1-013.

Design notes
------------
- Tokens are opaque 384-bit secrets; only their SHA-256 digest is persisted,
  so a database leak yields no usable tokens and audit/application logs never
  see token material.
- Rotation keeps ``family_id`` stable and atomically revokes the presented
  token (``replaced_by`` points at the successor) before the new token is
  usable. The revoke is a conditional UPDATE; when it affects zero rows the
  token was already rotated by a concurrent request, which is treated as
  replay and revokes the whole family.
- Presenting any already-rotated token (``revoked_at`` set with a
  ``replaced_by`` link) is also treated as reuse and revokes the family.
- Every failure surfaces as the same generic :class:`InvalidRefreshTokenError`
  so responses never reveal whether a user, session, or token exists.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.request_context import get_request_user_agent
from app.core.security import generate_refresh_token, hash_refresh_token
from app.models.refresh_token import RefreshToken
from app.models.user import User


class InvalidRefreshTokenError(ValueError):
    """Raised for expired, malformed, revoked, reused, or unknown tokens."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    """Tolerate naive datetimes (SQLite) and aware ones (PostgreSQL)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class RefreshTokenService:
    def issue(
        self,
        db: Session,
        user: User,
        *,
        family_id: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, RefreshToken]:
        """Create a new refresh session and return (raw_token, row).

        The raw token is returned exactly once and is never stored; the row
        keeps only its digest. Does not commit: callers own the transaction.
        """
        raw_token = generate_refresh_token()
        row = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            family_id=family_id or str(uuid4()),
            user_agent=user_agent if user_agent is not None else get_request_user_agent(),
            expires_at=_now() + timedelta(days=settings.refresh_token_expire_days),
        )
        db.add(row)
        db.flush()
        return raw_token, row

    def rotate(self, db: Session, raw_token: str) -> tuple[str, RefreshToken, User]:
        """Validate ``raw_token``, rotate it, and return the new session.

        Commits internally (a successful rotation is one transaction; a
        detected replay rolls back the pending new token before revoking the
        family in a fresh transaction).
        """
        now = _now()
        row = self._find(db, raw_token)

        if row is None:
            raise InvalidRefreshTokenError()

        if row.revoked_at is not None:
            if row.replaced_by is not None:
                # A rotated token presented again: reuse detected.
                self._revoke_family(db, row.family_id)
                db.commit()
            raise InvalidRefreshTokenError()

        if _as_utc(row.expires_at) <= now:
            raise InvalidRefreshTokenError()

        user = db.get(User, row.user_id)
        if user is None or user.is_locked():
            # Lockout is account-wide: a locked account cannot keep sessions
            # alive even with valid refresh tokens.
            raise InvalidRefreshTokenError()

        new_raw_token, new_row = self.issue(db, user, family_id=row.family_id)

        result = db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == row.id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now, replaced_by=new_row.id)
        )

        if result.rowcount == 0:
            # Concurrent rotation already revoked this token: replay detected.
            db.rollback()
            self._revoke_family(db, row.family_id)
            db.commit()
            raise InvalidRefreshTokenError()

        db.commit()
        return new_raw_token, new_row, user

    def revoke(self, db: Session, raw_token: str, *, user_id: int | None = None) -> bool:
        """Revoke one token (idempotent; no error for unknown/already revoked).

        When ``user_id`` is given, only that user's token is affected, so an
        authenticated caller can never revoke someone else's session.
        Commits internally.
        """
        row = self._find(db, raw_token)
        if row is None or row.revoked_at is not None:
            return False
        if user_id is not None and row.user_id != user_id:
            return False

        db.execute(update(RefreshToken).where(RefreshToken.id == row.id).values(revoked_at=_now()))
        db.commit()
        return True

    def revoke_all_for_user(self, db: Session, user_id: int) -> int:
        """Revoke every active refresh session of ``user_id``. Commits."""
        result = db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=_now())
        )
        db.commit()
        return result.rowcount

    def revoke_all_except(self, db: Session, user_id: int, kept_raw_token: str | None) -> int:
        """Revoke every active session of ``user_id`` except one (password change).

        Does not commit: the caller must commit so the revocation shares the
        password-change transaction. When ``kept_raw_token`` is missing or
        unknown, all sessions are revoked.
        """
        stmt = update(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
        if kept_raw_token:
            stmt = stmt.where(RefreshToken.token_hash != hash_refresh_token(kept_raw_token))
        return db.execute(stmt.values(revoked_at=_now())).rowcount

    def _revoke_family(self, db: Session, family_id: str) -> None:
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=_now())
        )

    def _find(self, db: Session, raw_token: str) -> RefreshToken | None:
        return db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
        ).scalar_one_or_none()
