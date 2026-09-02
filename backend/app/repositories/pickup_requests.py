from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.pickup_request_event import PickupRequestEvent
from app.models.user import User
from app.services.location import nearest_search


class PickupRequestRepository:
    def base_query(self, include_timeline: bool = False) -> Select[tuple[PickupRequest]]:
        statement = select(PickupRequest).options(
            selectinload(PickupRequest.citizen),
            selectinload(PickupRequest.assignment).selectinload(CollectorAssignment.collector),
            selectinload(PickupRequest.dispute),
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

    def get_by_id_for_update(
        self, db: Session, request_id: int, include_timeline: bool = False
    ) -> PickupRequest | None:
        """Lock the pickup request row with ``SELECT ... FOR UPDATE``.

        PostgreSQL will block concurrent transactions trying to lock the same
        row until the active transaction commits or rolls back. The
        ``collector_assignments.request_id`` unique constraint remains the
        ultimate guarantee that two collectors cannot both win acceptance.
        """
        statement = self.base_query(include_timeline=include_timeline).where(
            PickupRequest.id == request_id
        )
        return db.execute(statement.with_for_update()).unique().scalar_one_or_none()

    def get_by_id_with_dispute_for_update(
        self, db: Session, request_id: int, include_timeline: bool = False
    ) -> PickupRequest | None:
        """Lock the pickup request row, eagerly loading the dispute.

        Used by the citizen weight verification / dispute path (WIQ-V1-053).
        The row lock serialises concurrent confirm + dispute submissions so
        that a pickup cannot be transitioned to both ``completed`` and
        ``disputed`` by interleaving requests. PostgreSQL ``SELECT ...
        FOR UPDATE`` blocks the second transaction until the first commits
        or rolls back; the second transaction then re-reads the new status
        and is rejected by the state-machine guard. SQLite accepts the
        syntax but does not actually block — tests therefore exercise the
        state-machine guard on a single session.
        """
        from app.models.pickup_dispute import PickupDispute

        statement = (
            self.base_query(include_timeline=include_timeline)
            .options(selectinload(PickupRequest.dispute).selectinload(PickupDispute.resolved_by))
            .where(PickupRequest.id == request_id)
        )
        return db.execute(statement.with_for_update()).unique().scalar_one_or_none()

    def create(self, db: Session, pickup_request: PickupRequest) -> PickupRequest:
        db.add(pickup_request)
        db.flush()
        return pickup_request

    def add_status_event(
        self,
        db: Session,
        pickup_request: PickupRequest,
        status_value: PickupStatus,
        note: str,
        actor: User | None = None,
    ) -> None:
        db.add(
            PickupRequestEvent(
                request_id=pickup_request.id,
                actor_id=actor.id if actor is not None else None,
                status=status_value,
                note=note,
            )
        )

    def nearby_pickups_with_distance(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> list[tuple[PickupRequest, float]]:
        """Pending (unassigned) pickup requests within ``radius_km`` of a point.

        Returns ``(pickup_request, distance_km)`` pairs sorted nearest-first.
        """
        statement = self.base_query().where(
            PickupRequest.status == PickupStatus.pending,
            ~PickupRequest.assignment.has(),
        )
        requests = db.execute(statement).unique().scalars().all()
        scored = nearest_search(
            latitude,
            longitude,
            [(request.latitude, request.longitude) for request in requests],
            radius_km,
        )
        return [(requests[index], distance_km) for index, distance_km in scored]
