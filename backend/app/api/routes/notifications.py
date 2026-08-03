from fastapi import APIRouter, Depends, HTTPException, Query, Response, status as http_status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.notification import NotificationStatus
from app.models.user import User
from app.schemas.notification import (
    NotificationBulkActionRead,
    NotificationPageRead,
    NotificationRead,
    NotificationUnreadCountRead,
)
from app.services.notifications import NotificationService

router = APIRouter()

ALL_ROLES = ("citizen", "collector", "dealer", "admin")

_notification_service = NotificationService()


@router.get("", response_model=NotificationPageRead)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationPageRead:
    parsed_status = None
    if status is not None:
        try:
            parsed_status = NotificationStatus(status)
        except ValueError as exc:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification status: {status}",
            ) from exc
    return _notification_service.list_user(
        db, current_user, page=page, page_size=page_size, status_value=parsed_status
    )


@router.get("/unread/count", response_model=NotificationUnreadCountRead)
def unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationUnreadCountRead:
    return _notification_service.count_unread(db, current_user)


@router.get("/unread", response_model=list[NotificationRead])
def list_unread_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[NotificationRead]:
    return _notification_service.list_unread(db, current_user, limit=limit)


@router.post("/read-all", response_model=NotificationBulkActionRead)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationBulkActionRead:
    return _notification_service.mark_all_read(db, current_user)


@router.delete("/read", response_model=NotificationBulkActionRead)
def delete_read_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationBulkActionRead:
    return _notification_service.delete_read(db, current_user)


@router.get("/{notification_id}", response_model=NotificationRead)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationRead:
    return _notification_service.get_user(db, current_user, notification_id)


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationRead:
    return _notification_service.mark_read(db, current_user, notification_id)


@router.delete("/{notification_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> Response:
    _notification_service.delete(db, current_user, notification_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
