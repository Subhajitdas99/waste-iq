from datetime import datetime
from typing import Any, Sequence

from sqlalchemy.orm import Session

from app.core.request_context import get_request_ip, get_request_user_agent
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit import AuditLogRepository

# Keys that must never be persisted in audit before/after snapshots, even when
# a caller accidentally passes a snapshot that contains them.
SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "hashed_password",
        "access_token",
        "refresh_token",
        "token",
        "secret",
        "secret_key",
        "authorization",
    }
)


def sanitize_snapshot(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a copy of `snapshot` with sensitive keys removed (top level)."""
    if snapshot is None:
        return None
    return {key: value for key, value in snapshot.items() if key not in SENSITIVE_KEYS}


class AuditService:
    """Records append-only audit events synchronously with the triggering
    transaction.

    Records are added to the caller's active database session, so they commit
    or roll back together with the action they describe. When a caller does not
    provide request metadata, the IP address and user agent captured by the
    request middleware are used.
    """

    def __init__(self, repository: AuditLogRepository | None = None) -> None:
        self._repository = repository or AuditLogRepository()

    def record(
        self,
        db: Session,
        *,
        actor_user_id: int | None,
        action: str,
        resource: str,
        resource_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return self._repository.create(
            db,
            actor_user_id=actor_user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            before=sanitize_snapshot(before),
            after=sanitize_snapshot(after),
            ip_address=ip_address if ip_address is not None else get_request_ip(),
            user_agent=user_agent if user_agent is not None else get_request_user_agent(),
        )

    def record_for_user(
        self,
        db: Session,
        user: User,
        *,
        action: str,
        resource: str,
        resource_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> AuditLog:
        return self.record(
            db,
            actor_user_id=user.id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            before=before,
            after=after,
        )

    def list(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 50,
        actor_user_id: int | None = None,
        action: str | None = None,
        resource: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> tuple[Sequence[AuditLog], int, int]:
        return self._repository.list(
            db,
            page=page,
            page_size=page_size,
            actor_user_id=actor_user_id,
            action=action,
            resource=resource,
            created_after=created_after,
            created_before=created_before,
        )

    def login_history(
        self,
        db: Session,
        *,
        actor_user_id: int | None = None,
        outcome: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[AuditLog], int, int]:
        """List login-attempt records (WIQ-V1-019), newest first.

        Thin wrapper over ``AuditLogRepository.list_login_events``; see that
        method for the query semantics. ``actor_user_id`` must be supplied by
        the caller — routes derive it from the authenticated principal.
        """
        return self._repository.list_login_events(
            db,
            actor_user_id=actor_user_id,
            outcome=outcome,
            created_after=created_after,
            created_before=created_before,
            page=page,
            page_size=page_size,
        )
