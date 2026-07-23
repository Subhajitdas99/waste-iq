from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.pickup_request_event import PickupRequestEvent
from app.models.user import User


class PickupRequestRepository:
    def base_query(self, include_timeline: bool = False):
        statement = select(PickupRequest).options(
            selectinload(PickupRequest.citizen),
            selectinload(PickupRequest.assignment).selectinload(CollectorAssignment.collector),
        )
        if include_timeline:
            statement = statement.options(
                selectinload(PickupRequest.events).selectinload(PickupRequestEvent.actor)
            )
        return statement

    def get_by_id(
        self, db: Session, request_id: int, include_timeline: bool = False
    ) -> PickupRequest | None:
        statement = self.base_query(include_timeline=include_timeline).where(
            PickupRequest.id == request_id
        )
        return db.execute(statement).unique().scalar_one_or_none()

    def create(self, db: Session, request: PickupRequest) -> PickupRequest:
        db.add(request)
        db.flush()
        return request

    def add_status_event(
        self,
        db: Session,
        request: PickupRequest,
        status_value: PickupStatus,
        note: str,
        actor: User | None = None,
    ) -> None:
        db.add(
            PickupRequestEvent(
                request_id=request.id,
                actor_id=actor.id if actor is not None else None,
                status=status_value,
                note=note,
            )
        )
