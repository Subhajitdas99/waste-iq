from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.schemas.dealer import AdminDealerSummaryRead, DealerVerificationActionRead
from app.schemas.admin import AnalyticsRead
from app.schemas.user import UserRead
from app.services.admin import get_analytics, list_users
from app.services.dealer_profiles import (
    approve_dealer_profile,
    list_dealers_for_admin,
    reject_dealer_profile,
)

router = APIRouter()


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
) -> list[UserRead]:
    return [UserRead.model_validate(user) for user in list_users(db)]


@router.get("/analytics", response_model=AnalyticsRead)
def admin_analytics(
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
) -> AnalyticsRead:
    return get_analytics(db)


@router.get("/dealers", response_model=list[AdminDealerSummaryRead])
def admin_list_dealers(
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
) -> list[AdminDealerSummaryRead]:
    return list_dealers_for_admin(db)


@router.post("/dealers/{dealer_user_id}/approve", response_model=DealerVerificationActionRead)
def admin_approve_dealer(
    dealer_user_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
) -> DealerVerificationActionRead:
    return approve_dealer_profile(db, dealer_user_id)


@router.post("/dealers/{dealer_user_id}/reject", response_model=DealerVerificationActionRead)
def admin_reject_dealer(
    dealer_user_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
) -> DealerVerificationActionRead:
    return reject_dealer_profile(db, dealer_user_id)
