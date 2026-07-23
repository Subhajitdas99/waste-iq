from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User, UserRole
from app.schemas.admin import AnalyticsRead, RequestStatusBreakdown, RoleBreakdown


def list_users(db: Session) -> list[User]:
    statement = select(User).order_by(User.created_at.desc())
    return list(db.execute(statement).scalars().all())


def get_analytics(db: Session) -> AnalyticsRead:
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_pickup_requests = db.scalar(select(func.count(PickupRequest.id))) or 0
    total_completed_pickups = (
        db.scalar(
            select(func.count(PickupRequest.id)).where(
                PickupRequest.status == PickupStatus.completed
            )
        )
        or 0
    )
    total_collected_weight = (
        db.scalar(select(func.coalesce(func.sum(CollectorAssignment.weight_kg), 0.0))) or 0.0
    )

    def user_count(role: UserRole) -> int:
        return db.scalar(select(func.count(User.id)).where(User.role == role)) or 0

    def request_count(status: PickupStatus) -> int:
        return (
            db.scalar(select(func.count(PickupRequest.id)).where(PickupRequest.status == status))
            or 0
        )

    return AnalyticsRead(
        total_users=total_users,
        total_pickup_requests=total_pickup_requests,
        total_completed_pickups=total_completed_pickups,
        total_collected_weight_kg=round(float(total_collected_weight), 2),
        users_by_role=RoleBreakdown(
            citizens=user_count(UserRole.citizen),
            collectors=user_count(UserRole.collector),
            dealers=user_count(UserRole.dealer),
            admins=user_count(UserRole.admin),
        ),
        requests_by_status=RequestStatusBreakdown(
            pending=request_count(PickupStatus.pending),
            accepted=request_count(PickupStatus.accepted),
            on_the_way=request_count(PickupStatus.on_the_way),
            collected=request_count(PickupStatus.collected),
            completed=request_count(PickupStatus.completed),
            cancelled=request_count(PickupStatus.cancelled),
        ),
    )
