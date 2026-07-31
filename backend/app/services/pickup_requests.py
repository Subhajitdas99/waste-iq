from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User
from app.repositories.pickup_requests import PickupRequestRepository
from app.schemas.pickup_request import (
    CitizenRequestSummaryRead,
    CollectorAssignmentRead,
    NearbyPickupRequestRead,
    PickupRequestCreate,
    PickupRequestDetailRead,
    PickupRequestRead,
    PickupRequestTimelineEventRead,
    PickupRequestUpdate,
)
from app.services.location import calculate_distance_km
from app.services.stats import count_pickups_for_user

_repository = PickupRequestRepository()


def _serialize_assignment(pickup_request: PickupRequest) -> CollectorAssignmentRead | None:
    if pickup_request.assignment is None:
        return None

    return CollectorAssignmentRead(
        id=pickup_request.assignment.id,
        collector_id=pickup_request.assignment.collector_id,
        collector_name=pickup_request.assignment.collector.name,
        accepted_at=pickup_request.assignment.accepted_at,
        completed_at=pickup_request.assignment.completed_at,
        weight_kg=pickup_request.assignment.weight_kg,
    )


def _to_schema(pickup_request: PickupRequest) -> PickupRequestRead:
    assignment = _serialize_assignment(pickup_request)

    return PickupRequestRead(
        id=pickup_request.id,
        user_id=pickup_request.user_id,
        citizen_name=pickup_request.citizen.name,
        citizen_phone=pickup_request.citizen.phone,
        waste_type=pickup_request.waste_type,
        category=pickup_request.category,
        confidence=pickup_request.confidence,
        image_url=pickup_request.image_url,
        address=pickup_request.address,
        latitude=pickup_request.latitude,
        longitude=pickup_request.longitude,
        estimated_weight_kg=pickup_request.estimated_weight_kg,
        preferred_time=pickup_request.preferred_time,
        notes=pickup_request.notes,
        status=pickup_request.status.value,
        created_at=pickup_request.created_at,
        assigned_collector_name=assignment.collector_name if assignment is not None else None,
        can_cancel=pickup_request.status == PickupStatus.pending,
        assignment=assignment,
    )


def _to_nearby_schema(pickup_request: PickupRequest, distance_km: float) -> NearbyPickupRequestRead:
    return NearbyPickupRequestRead(
        **_to_schema(pickup_request).model_dump(), distance_km=distance_km
    )


def _to_detail_schema(pickup_request: PickupRequest) -> PickupRequestDetailRead:
    base = _to_schema(pickup_request)
    timeline = [
        PickupRequestTimelineEventRead(
            id=event.id,
            status=event.status.value,
            note=event.note,
            created_at=event.created_at,
            actor_name=event.actor.name if event.actor is not None else None,
            actor_role=event.actor.role.value if event.actor is not None else None,
        )
        for event in pickup_request.events
    ]
    return PickupRequestDetailRead(**base.model_dump(), timeline=timeline)


def _enforce_request_access(pickup_request: PickupRequest, user: User) -> None:
    if user.role == "citizen" and pickup_request.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this pickup request"
        )
    if user.role == "collector":
        assigned_to_user = (
            pickup_request.assignment is not None
            and pickup_request.assignment.collector_id == user.id
        )
        if pickup_request.status != PickupStatus.pending and not assigned_to_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this pickup request"
            )


def _available_pickup_filter():
    """Pending requests that no collector has accepted yet."""
    return [
        PickupRequest.status == PickupStatus.pending,
        ~PickupRequest.assignment.has(),
    ]


def _reload_pickup_or_500(db: Session, request_id: int) -> PickupRequest:
    reloaded = _repository.get_by_id(db, request_id)
    if reloaded is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pickup request could not be reloaded after update",
        )
    return reloaded


def _ensure_assigned_collector(pickup_request: PickupRequest, collector: User) -> None:
    if pickup_request.assignment is None or pickup_request.assignment.collector_id != collector.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This request is not assigned to you"
        )


def _get_request_for_assigned_collector(
    db: Session, request_id: int, collector: User
) -> PickupRequest:
    """Load a pickup and enforce that the collector is its assigned collector."""
    pickup_request = _repository.get_by_id(db, request_id)
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    _ensure_assigned_collector(pickup_request, collector)
    return pickup_request


def _require_status(pickup_request: PickupRequest, expected: PickupStatus, detail: str) -> None:
    if pickup_request.status != expected:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def create_pickup_request(
    db: Session,
    citizen: User,
    payload: PickupRequestCreate,
    category: str | None = None,
    confidence: float | None = None,
) -> PickupRequestRead:
    pickup_request = PickupRequest(
        user_id=citizen.id,
        category=category,
        confidence=confidence,
        **payload.model_dump(mode="python"),
    )
    _repository.create(db, pickup_request)
    _repository.add_status_event(
        db, pickup_request, PickupStatus.pending, "Pickup request created.", actor=citizen
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))


def list_pickup_requests_for_user(db: Session, user: User) -> list[PickupRequestRead]:
    statement = _repository.base_query().order_by(PickupRequest.created_at.desc())

    if user.role == "citizen":
        statement = statement.where(PickupRequest.user_id == user.id)
    elif user.role == "collector":
        statement = statement.outerjoin(CollectorAssignment).where(
            or_(
                PickupRequest.status == PickupStatus.pending,
                CollectorAssignment.collector_id == user.id,
            )
        )

    requests = db.execute(statement).unique().scalars().all()
    return [_to_schema(item) for item in requests]


def list_available_pickup_requests_for_collector(db: Session) -> list[PickupRequestRead]:
    statement = (
        _repository.base_query()
        .where(*_available_pickup_filter())
        .order_by(PickupRequest.created_at.desc())
    )

    requests = db.execute(statement).unique().scalars().all()
    return [_to_schema(item) for item in requests]


def list_nearby_pickup_requests_for_collector(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 5,
) -> list[NearbyPickupRequestRead]:
    statement = _repository.base_query().where(*_available_pickup_filter())

    requests = db.execute(statement).unique().scalars().all()
    nearby_requests = [
        (
            pickup_request,
            calculate_distance_km(
                latitude,
                longitude,
                pickup_request.latitude,
                pickup_request.longitude,
            ),
        )
        for pickup_request in requests
    ]
    nearby_requests = [
        (pickup_request, distance_km)
        for pickup_request, distance_km in nearby_requests
        if distance_km <= radius_km
    ]
    nearby_requests.sort(key=lambda item: item[1])

    return [
        _to_nearby_schema(pickup_request, distance_km)
        for pickup_request, distance_km in nearby_requests
    ]


def list_assigned_pickup_requests_for_collector(
    db: Session, collector: User
) -> list[PickupRequestRead]:
    statement = (
        _repository.base_query()
        .join(CollectorAssignment)
        .where(
            CollectorAssignment.collector_id == collector.id,
            PickupRequest.status.in_(
                [
                    PickupStatus.accepted,
                    PickupStatus.on_the_way,
                    PickupStatus.collected,
                    PickupStatus.completed,
                ]
            ),
        )
        .order_by(PickupRequest.created_at.desc())
    )

    requests = db.execute(statement).unique().scalars().all()
    return [_to_schema(item) for item in requests]


def get_pickup_request_for_user(
    db: Session, request_id: int, user: User
) -> PickupRequestDetailRead | None:
    pickup_request = _repository.get_by_id(db, request_id, include_timeline=True)
    if pickup_request is None:
        return None

    _enforce_request_access(pickup_request, user)
    return _to_detail_schema(pickup_request)


def get_pickup_request_for_collector(
    db: Session, collector: User, request_id: int
) -> PickupRequestDetailRead:
    """Full pickup detail with timeline, visible to collectors who can work the request.

    Collectors may view any pending (unassigned) request from the available queue,
    but assigned requests are only visible to the assigned collector.
    """
    pickup_request = _repository.get_by_id(db, request_id, include_timeline=True)
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )

    _enforce_request_access(pickup_request, collector)
    return _to_detail_schema(pickup_request)


def cancel_pickup_request_assignment(
    db: Session, collector: User, request_id: int
) -> PickupRequestRead:
    """Collector releases an accepted request back to the available queue.

    Only allowed before the trip starts (status == accepted). The assignment is
    deleted, the pickup returns to `pending`, and the release is recorded on the
    timeline with the collector as actor.
    """
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)
    _require_status(
        pickup_request,
        PickupStatus.accepted,
        "Only accepted requests can be cancelled",
    )

    db.delete(pickup_request.assignment)
    pickup_request.status = PickupStatus.pending
    pickup_request.assignment = None
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.pending,
        "Collector cancelled the assignment. Request is available again.",
        actor=collector,
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))


def get_citizen_request_summary(db: Session, citizen: User) -> CitizenRequestSummaryRead:
    return CitizenRequestSummaryRead(
        total_requests=count_pickups_for_user(db, citizen.id),
        pending_requests=count_pickups_for_user(db, citizen.id, PickupStatus.pending),
        accepted_requests=count_pickups_for_user(db, citizen.id, PickupStatus.accepted),
        completed_requests=count_pickups_for_user(db, citizen.id, PickupStatus.completed),
    )


def update_pickup_request(
    db: Session,
    request_id: int,
    user: User,
    payload: PickupRequestUpdate,
) -> PickupRequestRead | None:
    pickup_request = _repository.get_by_id(db, request_id)
    if pickup_request is None:
        return None

    previous_status = pickup_request.status
    update_data = payload.model_dump(exclude_unset=True, mode="json")
    next_status = None

    if user.role == "citizen":
        if pickup_request.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot update this pickup request",
            )
        if pickup_request.status != PickupStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending pickup requests can be edited",
            )
        update_data.pop("status", None)
    elif user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot update this pickup request"
        )

    if "status" in update_data:
        try:
            next_status = PickupStatus(update_data["status"])
            update_data["status"] = next_status
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value"
            ) from exc

    for field, value in update_data.items():
        setattr(pickup_request, field, value)

    if next_status is not None and next_status != previous_status:
        _repository.add_status_event(
            db, pickup_request, next_status, f"Status updated to {next_status.value}.", actor=user
        )

    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))


def accept_pickup_request(db: Session, collector: User, request_id: int) -> PickupRequestRead:
    pickup_request = _repository.get_by_id(db, request_id)
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    if pickup_request.status != PickupStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup request is no longer available"
        )
    if pickup_request.user_id == collector.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collectors cannot accept their own request",
        )

    assignment = CollectorAssignment(request_id=pickup_request.id, collector_id=collector.id)
    pickup_request.status = PickupStatus.accepted
    db.add(assignment)
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.accepted,
        "Collector accepted the pickup request.",
        actor=collector,
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))


def mark_pickup_request_on_the_way(
    db: Session, collector: User, request_id: int
) -> PickupRequestRead:
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)
    _require_status(pickup_request, PickupStatus.accepted, "Only accepted requests can be started")

    pickup_request.status = PickupStatus.on_the_way
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.on_the_way,
        "Collector is on the way.",
        actor=collector,
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))


def mark_pickup_request_collected(
    db: Session, collector: User, request_id: int
) -> PickupRequestRead:
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)
    _require_status(
        pickup_request,
        PickupStatus.on_the_way,
        "Only in-progress requests can be collected",
    )

    pickup_request.status = PickupStatus.collected
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.collected,
        "Waste has been collected and is awaiting final confirmation.",
        actor=collector,
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))


def complete_pickup_request(
    db: Session, collector: User, request_id: int, weight_kg: float
) -> PickupRequestRead:
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)
    _require_status(
        pickup_request,
        PickupStatus.collected,
        "Only collected requests can be completed",
    )

    pickup_request.status = PickupStatus.completed
    pickup_request.assignment.completed_at = datetime.now(timezone.utc)
    pickup_request.assignment.weight_kg = weight_kg
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.completed,
        f"Pickup completed with {round(weight_kg, 2)} kg reported.",
        actor=collector,
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))


def cancel_pickup_request(db: Session, citizen: User, request_id: int) -> PickupRequestRead | None:
    pickup_request = _repository.get_by_id(db, request_id)
    if pickup_request is None:
        return None
    if pickup_request.user_id != citizen.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot cancel this pickup request"
        )
    if pickup_request.status != PickupStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be cancelled"
        )

    pickup_request.status = PickupStatus.cancelled
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.cancelled,
        "Citizen cancelled the pickup request.",
        actor=citizen,
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id))
