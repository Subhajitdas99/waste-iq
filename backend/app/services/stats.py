"""Shared database aggregation helpers used across analytics services.

Centralizes the count/sum queries that were previously re-implemented in
``admin.py``, ``analytics.py``, ``collector_summary.py`` and
``pickup_requests.py`` so the shapes and defaults stay consistent.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User, UserRole


def count_users(db: Session, role: UserRole | None = None) -> int:
    statement = select(func.count(User.id))
    if role is not None:
        statement = statement.where(User.role == role)
    return db.scalar(statement) or 0


def count_pickups(db: Session, status_value: PickupStatus | None = None) -> int:
    statement = select(func.count(PickupRequest.id))
    if status_value is not None:
        statement = statement.where(PickupRequest.status == status_value)
    return db.scalar(statement) or 0


def count_pickups_for_user(
    db: Session, user_id: int, status_value: PickupStatus | None = None
) -> int:
    statement = select(func.count(PickupRequest.id)).where(PickupRequest.user_id == user_id)
    if status_value is not None:
        statement = statement.where(PickupRequest.status == status_value)
    return db.scalar(statement) or 0


def sum_collected_weight(db: Session, collector_id: int | None = None) -> float:
    statement = select(func.coalesce(func.sum(CollectorAssignment.weight_kg), 0.0))
    if collector_id is not None:
        statement = statement.where(CollectorAssignment.collector_id == collector_id)
    return float(db.scalar(statement) or 0.0)
