from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.pickup_request_event import PickupRequestEvent
from app.models.user import User
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


def _base_request_query(include_timeline: bool = False):
    statement = select(PickupRequest).options(
        selectinload(PickupRequest.citizen),
        selectinload(PickupRequest.assignment).selectinload(CollectorAssignment.collector),
    )
    if include_timeline:
        statement = statement.options(selectinload(PickupRequest.events).selectinload(PickupRequestEvent.actor))
    return statement


def _create_status_event(
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


def _serialize_assignment(request: PickupRequest) -> CollectorAssignmentRead | None:
    if request.assignment is None:
        return None

    return CollectorAssignmentRead(
        id=request.assignment.id,
        collector_id=request.assignment.collector_id,
        collector_name=request.assignment.collector.name,
        accepted_at=request.assignment.accepted_at,
        completed_at=request.assignment.completed_at,
        weight_kg=request.assignment.weight_kg,
    )


def _to_schema(request: PickupRequest) -> PickupRequestRead:
    assignment = _serialize_assignment(request)

    return PickupRequestRead(
        id=request.id,
        user_id=request.user_id,
        citizen_name=request.citizen.name,
        citizen_phone=request.citizen.phone,
        waste_type=request.waste_type,
        category=request.category,
        confidence=request.confidence,
        image_url=request.image_url,
        address=request.address,
        latitude=request.latitude,
        longitude=request.longitude,
        status=request.status.value,
        created_at=request.created_at,
        assigned_collector_name=assignment.collector_name if assignment is not None else None,
        can_cancel=request.status == PickupStatus.pending,
        assignment=assignment,
    )


def _to_nearby_schema(request: PickupRequest, distance_km: float) -> NearbyPickupRequestRead:
    return NearbyPickupRequestRead(**_to_schema(request).model_dump(), distance_km=distance_km)


def _to_detail_schema(request: PickupRequest) -> PickupRequestDetailRead:
    base = _to_schema(request)
    timeline = [
        PickupRequestTimelineEventRead(
            id=event.id,
            status=event.status.value,
            note=event.note,
            created_at=event.created_at,
            actor_name=event.actor.name if event.actor is not None else None,
            actor_role=event.actor.role.value if event.actor is not None else None,
        )
        for event in request.events
    ]
    return PickupRequestDetailRead(**base.model_dump(), timeline=timeline)


def _load_request(db: Session, request_id: int, include_timeline: bool = False) -> PickupRequest | None:
    return (
        db.execute(_base_request_query(include_timeline=include_timeline).where(PickupRequest.id == request_id))
        .unique()
        .scalar_one_or_none()
    )


def _enforce_request_access(request: PickupRequest, user: User) -> None:
    if user.role == "citizen" and request.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this pickup request")
    if user.role == "collector":
        assigned_to_user = request.assignment is not None and request.assignment.collector_id == user.id
        if request.status != PickupStatus.pending and not assigned_to_user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this pickup request")


def create_pickup_request(
    db: Session, 
    citizen: User, 
    payload: PickupRequestCreate,
    category: str | None = None,
    confidence: float | None = None,
) -> PickupRequestRead:
    request = PickupRequest(
        user_id=citizen.id, 
        category=category,
        confidence=confidence,
        **payload.model_dump(mode="json")
    )
    db.add(request)
    db.flush()
    _create_status_event(db, request, PickupStatus.pending, "Pickup request created.", actor=citizen)
    db.commit()
    request = _load_request(db, request.id)
    assert request is not None
    return _to_schema(request)


def list_pickup_requests_for_user(db: Session, user: User) -> list[PickupRequestRead]:
    statement = _base_request_query().order_by(PickupRequest.created_at.desc())

    if user.role == "citizen":
        statement = statement.where(PickupRequest.user_id == user.id)
    elif user.role == "collector":
        statement = (
            statement.outerjoin(CollectorAssignment)
            .where(
                or_(
                    PickupRequest.status == PickupStatus.pending,
                    CollectorAssignment.collector_id == user.id,
                )
            )
        )

    requests = db.execute(statement).unique().scalars().all()
    return [_to_schema(item) for item in requests]


def list_available_pickup_requests_for_collector(db: Session) -> list[PickupRequestRead]:
    statement = (
        _base_request_query()
        .where(
            PickupRequest.status == PickupStatus.pending,
            ~PickupRequest.assignment.has(),
        )
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
    statement = _base_request_query().where(
        PickupRequest.status == PickupStatus.pending,
        ~PickupRequest.assignment.has(),
    )

    requests = db.execute(statement).unique().scalars().all()
    nearby_requests = [
        (request, calculate_distance_km(latitude, longitude, request.latitude, request.longitude))
        for request in requests
    ]
    nearby_requests = [
        (request, distance_km)
        for request, distance_km in nearby_requests
        if distance_km <= radius_km
    ]
    nearby_requests.sort(key=lambda item: item[1])

    return [_to_nearby_schema(request, distance_km) for request, distance_km in nearby_requests]


def list_assigned_pickup_requests_for_collector(db: Session, collector: User) -> list[PickupRequestRead]:
    statement = (
        _base_request_query()
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


def get_pickup_request_for_user(db: Session, request_id: int, user: User) -> PickupRequestDetailRead | None:
    request = _load_request(db, request_id, include_timeline=True)
    if request is None:
        return None

    _enforce_request_access(request, user)
    return _to_detail_schema(request)


def get_citizen_request_summary(db: Session, citizen: User) -> CitizenRequestSummaryRead:
    total_requests = db.scalar(select(func.count(PickupRequest.id)).where(PickupRequest.user_id == citizen.id)) or 0
    pending_requests = (
        db.scalar(
            select(func.count(PickupRequest.id)).where(
                PickupRequest.user_id == citizen.id,
                PickupRequest.status == PickupStatus.pending,
            )
        )
        or 0
    )
    accepted_requests = (
        db.scalar(
            select(func.count(PickupRequest.id)).where(
                PickupRequest.user_id == citizen.id,
                PickupRequest.status == PickupStatus.accepted,
            )
        )
        or 0
    )
    completed_requests = (
        db.scalar(
            select(func.count(PickupRequest.id)).where(
                PickupRequest.user_id == citizen.id,
                PickupRequest.status == PickupStatus.completed,
            )
        )
        or 0
    )

    return CitizenRequestSummaryRead(
        total_requests=total_requests,
        pending_requests=pending_requests,
        accepted_requests=accepted_requests,
        completed_requests=completed_requests,
    )


def update_pickup_request(
    db: Session,
    request_id: int,
    user: User,
    payload: PickupRequestUpdate,
) -> PickupRequestRead | None:
    request = _load_request(db, request_id)
    if request is None:
        return None

    previous_status = request.status
    update_data = payload.model_dump(exclude_unset=True, mode="json")
    next_status = None

    if user.role == "citizen":
        if request.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot update this pickup request")
        if request.status != PickupStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending pickup requests can be edited",
            )
        update_data.pop("status", None)
    elif user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot update this pickup request")

    if "status" in update_data:
        try:
            next_status = PickupStatus(update_data["status"])
            update_data["status"] = next_status
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value") from exc

    for field, value in update_data.items():
        setattr(request, field, value)

    if next_status is not None and next_status != previous_status:
        _create_status_event(db, request, next_status, f"Status updated to {next_status.value}.", actor=user)

    db.commit()
    request = _load_request(db, request.id)
    assert request is not None
    return _to_schema(request)


def accept_pickup_request(db: Session, collector: User, request_id: int) -> PickupRequestRead:
    request = _load_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    if request.status != PickupStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup request is no longer available")
    if request.user_id == collector.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collectors cannot accept their own request")

    assignment = CollectorAssignment(request_id=request.id, collector_id=collector.id)
    request.status = PickupStatus.accepted
    db.add(assignment)
    _create_status_event(db, request, PickupStatus.accepted, "Collector accepted the pickup request.", actor=collector)
    db.commit()
    request = _load_request(db, request.id)
    assert request is not None
    return _to_schema(request)


def mark_pickup_request_on_the_way(db: Session, collector: User, request_id: int) -> PickupRequestRead:
    request = _load_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    if request.assignment is None or request.assignment.collector_id != collector.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request is not assigned to you")
    if request.status != PickupStatus.accepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only accepted requests can be started")

    request.status = PickupStatus.on_the_way
    _create_status_event(db, request, PickupStatus.on_the_way, "Collector is on the way.", actor=collector)
    db.commit()
    request = _load_request(db, request.id)
    assert request is not None
    return _to_schema(request)


def mark_pickup_request_collected(db: Session, collector: User, request_id: int) -> PickupRequestRead:
    request = _load_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    if request.assignment is None or request.assignment.collector_id != collector.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request is not assigned to you")
    if request.status != PickupStatus.on_the_way:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only in-progress requests can be collected")

    request.status = PickupStatus.collected
    _create_status_event(db, request, PickupStatus.collected, "Waste has been collected and is awaiting final confirmation.", actor=collector)
    db.commit()
    request = _load_request(db, request.id)
    assert request is not None
    return _to_schema(request)


def complete_pickup_request(db: Session, collector: User, request_id: int, weight_kg: float) -> PickupRequestRead:
    request = _load_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    if request.assignment is None or request.assignment.collector_id != collector.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request is not assigned to you")
    if request.status != PickupStatus.collected:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only collected requests can be completed")

    request.status = PickupStatus.completed
    request.assignment.completed_at = datetime.now(timezone.utc)
    request.assignment.weight_kg = weight_kg
    _create_status_event(
        db,
        request,
        PickupStatus.completed,
        f"Pickup completed with {round(weight_kg, 2)} kg reported.",
        actor=collector,
    )
    db.commit()
    request = _load_request(db, request.id)
    assert request is not None
    return _to_schema(request)


def cancel_pickup_request(db: Session, citizen: User, request_id: int) -> PickupRequestRead | None:
    request = _load_request(db, request_id)
    if request is None:
        return None
    if request.user_id != citizen.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot cancel this pickup request")
    if request.status != PickupStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be cancelled")

    request.status = PickupStatus.cancelled
    _create_status_event(db, request, PickupStatus.cancelled, "Citizen cancelled the pickup request.", actor=citizen)
    db.commit()
    request = _load_request(db, request.id)
    assert request is not None
    return _to_schema(request)
