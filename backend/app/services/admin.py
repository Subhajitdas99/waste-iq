from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pickup_request import PickupStatus
from app.models.user import User, UserRole
from app.schemas.admin import AnalyticsRead, RequestStatusBreakdown, RoleBreakdown
from app.services.stats import count_pickups, count_users, sum_collected_weight


def list_users(db: Session) -> list[User]:
    statement = select(User).order_by(User.created_at.desc())
    return list(db.execute(statement).scalars().all())


def get_analytics(db: Session) -> AnalyticsRead:
    return AnalyticsRead(
        total_users=count_users(db),
        total_pickup_requests=count_pickups(db),
        total_completed_pickups=count_pickups(db, PickupStatus.completed),
        total_collected_weight_kg=round(sum_collected_weight(db), 2),
        users_by_role=RoleBreakdown(
            citizens=count_users(db, UserRole.citizen),
            collectors=count_users(db, UserRole.collector),
            dealers=count_users(db, UserRole.dealer),
            admins=count_users(db, UserRole.admin),
        ),
        requests_by_status=RequestStatusBreakdown(
            pending=count_pickups(db, PickupStatus.pending),
            accepted=count_pickups(db, PickupStatus.accepted),
            on_the_way=count_pickups(db, PickupStatus.on_the_way),
            collected=count_pickups(db, PickupStatus.collected),
            completed=count_pickups(db, PickupStatus.completed),
            cancelled=count_pickups(db, PickupStatus.cancelled),
        ),
    )
