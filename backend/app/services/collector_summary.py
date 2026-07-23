from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User
from app.schemas.pickup_request import CollectorSummaryRead


def get_collector_summary(db: Session, collector: User) -> CollectorSummaryRead:
    """
    Aggregates this collector's assignment stats:
    - total_assigned: all requests ever assigned to them
    - active_jobs: accepted, on_the_way, or collected (not yet completed)
    - completed_jobs: status == completed
    - total_weight_kg: sum of weight_kg across completed jobs
    """
    total_assigned = (
        db.scalar(
            select(func.count(CollectorAssignment.id)).where(
                CollectorAssignment.collector_id == collector.id
            )
        )
        or 0
    )

    active_jobs = (
        db.scalar(
            select(func.count(PickupRequest.id))
            .join(CollectorAssignment, CollectorAssignment.request_id == PickupRequest.id)
            .where(
                CollectorAssignment.collector_id == collector.id,
                PickupRequest.status.in_(
                    [PickupStatus.accepted, PickupStatus.on_the_way, PickupStatus.collected]
                ),
            )
        )
        or 0
    )

    completed_jobs = (
        db.scalar(
            select(func.count(PickupRequest.id))
            .join(CollectorAssignment, CollectorAssignment.request_id == PickupRequest.id)
            .where(
                CollectorAssignment.collector_id == collector.id,
                PickupRequest.status == PickupStatus.completed,
            )
        )
        or 0
    )

    total_weight_kg = (
        db.scalar(
            select(func.coalesce(func.sum(CollectorAssignment.weight_kg), 0.0)).where(
                CollectorAssignment.collector_id == collector.id
            )
        )
        or 0.0
    )

    return CollectorSummaryRead(
        total_assigned=total_assigned,
        active_jobs=active_jobs,
        completed_jobs=completed_jobs,
        total_weight_kg=round(float(total_weight_kg), 2),
    )
