from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User
from app.schemas.pickup_request import (
    CollectorAssignmentRead,
    PickupRequestCreate,
    PickupRequestRead,
    PickupRequestUpdate,
)


def _base_request_query():
    return select(PickupRequest).options(
        selectinload(PickupRequest.citizen),
        selectinload(PickupRequest.assignment).selectinload(CollectorAssignment.collector),
    )


def _to_schema(request: PickupRequest) -> PickupRequestRead:
    assignment = None
    if request.assignment is not None:
        assignment = CollectorAssignmentRead(
            id=request.assignment.id,
            collector_id=request.assignment.collector_id,
            collector_name=request.assignment.collector.name,
            accepted_at=request.assignment.accepted_at,
            completed_at=request.assignment.completed_at,
            weight_kg=request.assignment.weight_kg,
        )

    return PickupRequestRead(
        id=request.id,
        user_id=request.user_id,
        citizen_name=request.citizen.name,
        waste_type=request.waste_type,
        photo_url=request.photo_url,
        address=request.address,
        latitude=request.latitude,
        longitude=request.longitude,
        status=request.status.value,
        created_at=request.created_at,
        assignment=assignment,
    )


def create_pickup_request(db: Session, citizen: User, payload: PickupRequestCreate) -> PickupRequestRead:
    request = PickupRequest(user_id=citizen.id, **payload.model_dump(mode="json"))
    db.add(request)
    db.commit()
    db.refresh(request)
    request = db.execute(_base_request_query().where(PickupRequest.id == request.id)).scalar_one()
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


def get_pickup_request_for_user(db: Session, request_id: int, user: User) -> PickupRequestRead | None:
    request = db.execute(_base_request_query().where(PickupRequest.id == request_id)).scalar_one_or_none()
    if request is None:
        return None

    if user.role == "citizen" and request.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this pickup request")
    if user.role == "collector":
        assigned_to_user = request.assignment is not None and request.assignment.collector_id == user.id
        if request.status != PickupStatus.pending and not assigned_to_user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this pickup request")

    return _to_schema(request)


def update_pickup_request(
    db: Session,
    request_id: int,
    user: User,
    payload: PickupRequestUpdate,
) -> PickupRequestRead | None:
    request = db.execute(_base_request_query().where(PickupRequest.id == request_id)).scalar_one_or_none()
    if request is None:
        return None

    update_data = payload.model_dump(exclude_unset=True, mode="json")

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
            update_data["status"] = PickupStatus(update_data["status"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value") from exc

    for field, value in update_data.items():
        setattr(request, field, value)

    db.commit()
    db.refresh(request)
    request = db.execute(_base_request_query().where(PickupRequest.id == request.id)).scalar_one()
    return _to_schema(request)


def accept_pickup_request(db: Session, collector: User, request_id: int) -> PickupRequestRead:
    request = db.execute(_base_request_query().where(PickupRequest.id == request_id)).scalar_one_or_none()
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    if request.status != PickupStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup request is no longer available")
    if request.user_id == collector.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collectors cannot accept their own request")

    assignment = CollectorAssignment(request_id=request.id, collector_id=collector.id)
    request.status = PickupStatus.accepted
    db.add(assignment)
    db.commit()
    db.refresh(request)
    request = db.execute(_base_request_query().where(PickupRequest.id == request.id)).scalar_one()
    return _to_schema(request)


def complete_pickup_request(db: Session, collector: User, request_id: int, weight_kg: float) -> PickupRequestRead:
    request = db.execute(_base_request_query().where(PickupRequest.id == request_id)).scalar_one_or_none()
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    if request.assignment is None or request.assignment.collector_id != collector.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request is not assigned to you")
    if request.status != PickupStatus.accepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only accepted requests can be completed")

    request.status = PickupStatus.completed
    request.assignment.completed_at = datetime.now(timezone.utc)
    request.assignment.weight_kg = weight_kg
    db.commit()
    db.refresh(request)
    request = db.execute(_base_request_query().where(PickupRequest.id == request.id)).scalar_one()
    return _to_schema(request)
