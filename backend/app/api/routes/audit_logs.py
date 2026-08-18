from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.audit import AuditLogPageRead, AuditLogRead
from app.services.audit import AuditService

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit Logs"])

_audit_service = AuditService()


@router.get("", response_model=AuditLogPageRead)
def admin_list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    actor_user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    resource: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> AuditLogPageRead:
    items, total_items, total_pages = _audit_service.list(
        db,
        page=page,
        page_size=page_size,
        actor_user_id=actor_user_id,
        action=action,
        resource=resource,
        created_after=created_after,
        created_before=created_before,
    )
    return AuditLogPageRead(
        items=[AuditLogRead.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
