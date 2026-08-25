import math
from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog

_LOGIN_ACTIONS: tuple[str, str] = ("login_success", "login_failure")
_OUTCOME_TO_ACTION: dict[str, str] = {
    "success": "login_success",
    "failure": "login_failure",
}


class AuditLogRepository:
    """Append-only persistence for audit records.

    Only creation and querying are exposed. Audit records must never be
    updated or deleted by application code.
    """

    def create(
        self,
        db: Session,
        *,
        actor_user_id: int | None,
        action: str,
        resource: str,
        resource_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        record = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            before=before,
            after=after,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(record)
        db.flush()
        return record

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
        statement = select(AuditLog)

        if actor_user_id is not None:
            statement = statement.where(AuditLog.actor_user_id == actor_user_id)
        if action is not None:
            statement = statement.where(AuditLog.action == action)
        if resource is not None:
            statement = statement.where(AuditLog.resource == resource)
        if created_after is not None:
            statement = statement.where(AuditLog.created_at >= created_after)
        if created_before is not None:
            statement = statement.where(AuditLog.created_at <= created_before)

        count_statement = select(func.count()).select_from(statement.subquery())
        total_items = db.scalar(count_statement) or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        statement = (
            statement.options(joinedload(AuditLog.actor))
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(db.execute(statement).scalars().all())

        return items, total_items, total_pages

    def list_login_events(
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
        """List login-attempt audit records (WIQ-V1-019), newest first.

        Only ``login_success`` / ``login_failure`` audit actions are visible
        through this query; all other audit activity is excluded. The caller
        supplies ``actor_user_id`` explicitly (the route derives it from the
        authenticated user) — identity is never inferred here.

        ``outcome`` is the public value ("success" / "failure") and is mapped
        to the corresponding internal action; unknown values raise
        ``ValueError`` so mistakes surface before a query runs.
        """
        statement = select(AuditLog).where(AuditLog.action.in_(_LOGIN_ACTIONS))

        if actor_user_id is not None:
            statement = statement.where(AuditLog.actor_user_id == actor_user_id)
        if outcome is not None:
            action = _OUTCOME_TO_ACTION.get(outcome)
            if action is None:
                raise ValueError("outcome must be 'success' or 'failure'")
            statement = statement.where(AuditLog.action == action)
        if created_after is not None:
            statement = statement.where(AuditLog.created_at >= created_after)
        if created_before is not None:
            statement = statement.where(AuditLog.created_at <= created_before)

        count_statement = select(func.count()).select_from(statement.subquery())
        total_items = db.scalar(count_statement) or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        statement = (
            statement.options(joinedload(AuditLog.actor))
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(db.execute(statement).scalars().all())

        return items, total_items, total_pages
