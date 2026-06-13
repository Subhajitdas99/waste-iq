from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.schemas.admin import AnalyticsRead
from app.schemas.user import UserRead
from app.services.admin import get_analytics, list_users

router = APIRouter()


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
) -> list[UserRead]:
    return list_users(db)


@router.get("/analytics", response_model=AnalyticsRead)
def admin_analytics(
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
) -> AnalyticsRead:
    return get_analytics(db)
