from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.admin import AnalyticsRead
from app.schemas.dealer import (
    AdminDealerDetailRead,
    AdminDealerListPageRead,
    DealerApprovalActionRead,
    DealerRejectRequest,
)
from app.schemas.notification import (
    NotificationBroadcastRead,
    NotificationBroadcastRequest,
)
from app.schemas.user import UserRead
from app.services.admin import get_analytics, list_users
from app.services.dealer_approval import AdminDealerApprovalService
from app.services.notifications import NotificationBroadcaster
from app.schemas.user import UserRead
from app.services.admin import get_analytics, list_users
from app.services.dealer_approval import AdminDealerApprovalService

router = APIRouter()

_admin_dealer_approval_service = AdminDealerApprovalService()
_notification_broadcaster = NotificationBroadcaster()


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[UserRead]:
    return [UserRead.model_validate(user) for user in list_users(db)]


@router.get("/analytics", response_model=AnalyticsRead)
def admin_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> AnalyticsRead:
    return get_analytics(db)


@router.get("/dealers", response_model=AdminDealerListPageRead)
def admin_list_dealers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_value: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> AdminDealerListPageRead:
    return _admin_dealer_approval_service.list_dealers(
        db,
        page=page,
        page_size=page_size,
        status_value=status_value,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/dealers/pending", response_model=AdminDealerListPageRead)
def admin_list_pending_dealers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> AdminDealerListPageRead:
    return _admin_dealer_approval_service.list_pending_dealers(
        db, page=page, page_size=page_size, search=search
    )


@router.get("/dealers/{dealer_user_id}", response_model=AdminDealerDetailRead)
def admin_get_dealer_detail(
    dealer_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> AdminDealerDetailRead:
    return _admin_dealer_approval_service.get_dealer_detail(db, dealer_user_id)


@router.post("/dealers/{dealer_user_id}/approve", response_model=DealerApprovalActionRead)
def admin_approve_dealer(
    dealer_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> DealerApprovalActionRead:
    return _admin_dealer_approval_service.approve_dealer(db, current_user, dealer_user_id)


@router.post("/dealers/{dealer_user_id}/reject", response_model=DealerApprovalActionRead)
def admin_reject_dealer(
    dealer_user_id: int,
    payload: DealerRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> DealerApprovalActionRead:
    return _admin_dealer_approval_service.reject_dealer(
        db, current_user, dealer_user_id, payload.reason
    )


@router.post("/notifications/broadcast", response_model=NotificationBroadcastRead)
def admin_broadcast_notification(
    payload: NotificationBroadcastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> NotificationBroadcastRead:
    return _notification_broadcaster.broadcast(db, payload=payload, broadcast_type=payload.type)
