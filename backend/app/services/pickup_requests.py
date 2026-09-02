from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_dispute import DisputeResolution, PickupDispute
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
    PickupDisputeRead,
    WeightDisputeResolveRequest,
)
from app.services.audit import AuditService
from app.services.notifications import NotificationDispatcher
from app.services.pickup_request_images import cleanup_pickup_request_images
from app.services.stats import count_pickups_for_user
from app.services.upload import ImageUploader

_repository = PickupRequestRepository()
_dispatcher = NotificationDispatcher()
_audit_service = AuditService()


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


def _should_expose_phone(pickup_request: PickupRequest, viewer: User | None) -> bool:
    if viewer is None:
        return False
    if getattr(viewer, "role", None) == "admin":
        return True
    if viewer.id == pickup_request.user_id:
        return True
    return False


def _to_schema(pickup_request: PickupRequest, viewer: User | None = None) -> PickupRequestRead:
    assignment = _serialize_assignment(pickup_request)
    citizen_phone = (
        pickup_request.citizen.phone if _should_expose_phone(pickup_request, viewer) else None
    )

    return PickupRequestRead(
        id=pickup_request.id,
        user_id=pickup_request.user_id,
        citizen_name=pickup_request.citizen.name,
        citizen_phone=citizen_phone,
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


def _to_nearby_schema(
    pickup_request: PickupRequest, distance_km: float, viewer: User | None = None
) -> NearbyPickupRequestRead:
    return NearbyPickupRequestRead(
        **_to_schema(pickup_request, viewer=viewer).model_dump(), distance_km=distance_km
    )


def _to_detail_schema(
    pickup_request: PickupRequest, viewer: User | None = None
) -> PickupRequestDetailRead:
    base = _to_schema(pickup_request, viewer=viewer)
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
    dispute = (
        PickupDisputeRead.model_validate(pickup_request.dispute)
        if pickup_request.dispute is not None
        else None
    )
    return PickupRequestDetailRead(**base.model_dump(), timeline=timeline, dispute=dispute)


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


def _record_audit(
    db: Session,
    actor: User,
    action: str,
    pickup_request: PickupRequest,
    *,
    after: dict | None = None,
    before: dict | None = None,
) -> None:
    _audit_service.record(
        db,
        actor_user_id=actor.id,
        action=action,
        resource="pickup_request",
        resource_id=str(pickup_request.id),
        before=before,
        after=after,
    )


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
    _dispatcher.notify_pickup_created(db, pickup_request)
    _record_audit(
        db,
        citizen,
        "pickup_created",
        pickup_request,
        after={"status": PickupStatus.pending.value},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=citizen)


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
    return [_to_schema(item, viewer=user) for item in requests]


def list_available_pickup_requests_for_collector(db: Session) -> list[PickupRequestRead]:
    statement = (
        _repository.base_query()
        .where(*_available_pickup_filter())
        .order_by(PickupRequest.created_at.desc())
    )

    requests = db.execute(statement).unique().scalars().all()
    return [_to_schema(item, viewer=None) for item in requests]


def list_nearby_pickup_requests_for_collector(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 5,
) -> list[NearbyPickupRequestRead]:
    nearby_requests = _repository.nearby_pickups_with_distance(db, latitude, longitude, radius_km)

    return [
        _to_nearby_schema(pickup_request, distance_km, viewer=None)
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
                    PickupStatus.weight_recorded,
                    PickupStatus.completed,
                ]
            ),
        )
        .order_by(PickupRequest.created_at.desc())
    )

    requests = db.execute(statement).unique().scalars().all()
    return [_to_schema(item, viewer=collector) for item in requests]


def get_pickup_request_for_user(
    db: Session, request_id: int, user: User
) -> PickupRequestDetailRead | None:
    pickup_request = _repository.get_by_id(db, request_id, include_timeline=True)
    if pickup_request is None:
        return None

    _enforce_request_access(pickup_request, user)
    return _to_detail_schema(pickup_request, viewer=user)


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
    return _to_detail_schema(pickup_request, viewer=collector)


def cancel_pickup_request_assignment(
    db: Session, collector: User, request_id: int
) -> PickupRequestRead:
    """Collector releases an accepted request back to the available queue.

    Only allowed before the trip starts (status == accepted). The assignment is
    deleted, the pickup returns to `pending`, and the release is recorded on the
    timeline with the collector as actor.
    """
    pickup_request = _repository.get_by_id(db, request_id)
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )

    is_assigned_to_collector = (
        pickup_request.assignment is not None
        and pickup_request.assignment.collector_id == collector.id
    )
    if not is_assigned_to_collector:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This request is not assigned to you"
        )

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
    _record_audit(
        db,
        collector,
        "pickup_assignment_released",
        pickup_request,
        after={"status": PickupStatus.pending.value},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=collector)


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
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=user)


def accept_pickup_request(db: Session, collector: User, request_id: int) -> PickupRequestRead:
    """Collector accepts a pending pickup.

    PostgreSQL ``SELECT ... FOR UPDATE`` is used to acquire a row-level lock on
    the pickup request before any state is checked or written. This serialises
    concurrent acceptance attempts at the database level, preventing a race where
    two collectors both read ``status == pending`` before either writes. The
    ``collector_assignments.request_id`` unique constraint is the fallback guard
    on the commit side; any constraint violation is surfaced as a 409 Conflict
    rather than a 500 Internal Server Error.

    Repeated calls from the assigned collector return the current resource
    unchanged (no duplicate assignment, no duplicate notification/audit).
    """
    pickup_request = _repository.get_by_id_for_update(db, request_id)
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )

    if pickup_request.user_id == collector.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collectors cannot accept their own request",
        )

    if pickup_request.assignment is not None:
        if pickup_request.assignment.collector_id == collector.id:
            return _to_schema(pickup_request, viewer=collector)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup request is no longer available"
        )

    if pickup_request.status != PickupStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup request is no longer available"
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
    _dispatcher.notify_pickup_accepted(db, pickup_request, collector)
    _record_audit(
        db,
        collector,
        "pickup_accepted",
        pickup_request,
        after={"status": PickupStatus.accepted.value},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pickup request is no longer available",
        ) from None
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=collector)


def mark_pickup_request_on_the_way(
    db: Session, collector: User, request_id: int
) -> PickupRequestRead:
    """Transition accepted -> on_the_way.

    Idempotent: returns current state if already on_the_way.
    """
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)

    if pickup_request.status == PickupStatus.on_the_way:
        return _to_schema(pickup_request, viewer=collector)

    _require_status(pickup_request, PickupStatus.accepted, "Only accepted requests can be started")

    pickup_request.status = PickupStatus.on_the_way
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.on_the_way,
        "Collector is on the way.",
        actor=collector,
    )
    _dispatcher.notify_pickup_started(db, pickup_request, collector)
    _record_audit(
        db,
        collector,
        "pickup_started",
        pickup_request,
        after={"status": PickupStatus.on_the_way.value},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=collector)


def mark_pickup_request_collected(
    db: Session, collector: User, request_id: int
) -> PickupRequestRead:
    """Transition on_the_way -> collected.

    Idempotent: returns current state if already collected.
    """
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)

    if pickup_request.status == PickupStatus.collected:
        return _to_schema(pickup_request, viewer=collector)

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
    _dispatcher.notify_pickup_collected(db, pickup_request, collector)
    _record_audit(
        db,
        collector,
        "pickup_collected",
        pickup_request,
        after={"status": PickupStatus.collected.value},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=collector)


def record_weight(
    db: Session, collector: User, request_id: int, weight_kg: float
) -> PickupRequestRead:
    """Transition collected -> weight_recorded.

    Records the measured weight on the assignment. The pickup enters the
    ``weight_recorded`` state, which is the integration boundary for
    WIQ-V1-046 (citizen verification). Final completion is deferred until
    the citizen confirms (or disputes) the recorded weight.

    Idempotent: a second call with the same weight is a no-op; a call with
    a different weight while already in ``weight_recorded`` is rejected to
    prevent silent overwrite.
    """
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)

    if pickup_request.status == PickupStatus.weight_recorded:
        existing = pickup_request.assignment.weight_kg if pickup_request.assignment else None
        if existing is not None and abs(existing - weight_kg) < 1e-6:
            return _to_schema(pickup_request, viewer=collector)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Weight already recorded for this pickup",
        )

    if pickup_request.status == PickupStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pickup is already completed",
        )

    _require_status(
        pickup_request,
        PickupStatus.collected,
        "Only collected requests can have a weight recorded",
    )

    pickup_request.status = PickupStatus.weight_recorded
    pickup_request.assignment.weight_kg = weight_kg
    pickup_request.assignment.completed_at = datetime.now(timezone.utc)
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.weight_recorded,
        f"Collector reported {round(weight_kg, 2)} kg. Awaiting citizen confirmation.",
        actor=collector,
    )
    _dispatcher.notify_weight_verification_pending(db, pickup_request, weight_kg)
    _record_audit(
        db,
        collector,
        "pickup_weight_recorded",
        pickup_request,
        after={"status": PickupStatus.weight_recorded.value, "weight_kg": weight_kg},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=collector)


def complete_pickup_request(
    db: Session, collector: User, request_id: int, weight_kg: float
) -> PickupRequestRead:
    """Final completion transition (legacy path).

    This path is preserved for admin or legacy scenarios only.
    The canonical collector workflow now requires citizen verification:

        collected -> record_weight -> (WIQ-V1-046 citizen verification) -> completed

    Only accepts `collected` (legacy) source state. Transitions from
    `weight_recorded` or `disputed` are not permitted through this endpoint;
    use the citizen verification or admin resolution flows instead.
    """
    pickup_request = _get_request_for_assigned_collector(db, request_id, collector)

    if pickup_request.status == PickupStatus.completed:
        return _to_schema(pickup_request, viewer=collector)

    if pickup_request.status not in (PickupStatus.collected,):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Pickup must be in collected state. "
                "Use citizen verification to complete after weight is recorded."
            ),
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
    _dispatcher.notify_pickup_completed(db, pickup_request, weight_kg)
    _record_audit(
        db,
        collector,
        "pickup_completed",
        pickup_request,
        after={"status": PickupStatus.completed.value, "weight_kg": weight_kg},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=collector)


def cancel_pickup_request(
    db: Session, citizen: User, request_id: int, uploader: ImageUploader
) -> PickupRequestRead | None:
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
    # Best-effort cleanup of the request's stored image assets. Provider
    # failures (including already-missing assets) never fail the cancellation.
    cleanup_pickup_request_images(db, pickup_request, uploader)
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.cancelled,
        "Citizen cancelled the pickup request.",
        actor=citizen,
    )
    _record_audit(
        db,
        citizen,
        "pickup_cancelled",
        pickup_request,
        after={"status": PickupStatus.cancelled.value},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=citizen)


# ─── WIQ-V1-046: Citizen Weight Verification & Dispute ───────────────────────


def _get_request_for_citizen(db: Session, request_id: int, citizen: User) -> PickupRequest:
    pickup_request = _repository.get_by_id(db, request_id, include_timeline=True)
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    if pickup_request.user_id != citizen.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot verify this pickup request",
        )
    return pickup_request


def _get_request_for_citizen_for_update(
    db: Session, request_id: int, citizen: User
) -> PickupRequest:
    """Citizen-scoped pickup loader that locks the row (WIQ-V1-053).

    Used by the weight verification / dispute endpoints. PostgreSQL
    ``SELECT ... FOR UPDATE`` serialises concurrent confirm + dispute
    attempts against the same pickup so they cannot both observe
    ``status == weight_recorded`` and write conflicting terminal states.
    """
    pickup_request = _repository.get_by_id_with_dispute_for_update(
        db, request_id, include_timeline=True
    )
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    if pickup_request.user_id != citizen.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot verify this pickup request",
        )
    return pickup_request


def confirm_pickup_weight(db: Session, citizen: User, request_id: int) -> PickupRequestRead:
    """Citizen confirms the collector-reported weight (WIQ-V1-046).

    The pickup row is locked with ``SELECT ... FOR UPDATE`` before the
    state-machine check so that a concurrent confirm + dispute (or two
    confirms) cannot both observe ``status == weight_recorded`` and
    produce conflicting terminal states (WIQ-V1-053). The first
    transaction wins; the second sees the new status and either returns
    idempotently (``completed``) or is rejected as a no-op (the dispute
    branch).

    Idempotent: a repeat confirmation when the pickup is already
    ``completed`` returns the current resource without creating a new
    event, audit row, or notification.
    """
    pickup_request = _get_request_for_citizen_for_update(db, request_id, citizen)

    if pickup_request.status == PickupStatus.completed:
        return _to_schema(pickup_request, viewer=citizen)

    if pickup_request.status == PickupStatus.disputed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pickup is already disputed and cannot be confirmed",
        )

    if pickup_request.status != PickupStatus.weight_recorded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Weight has not been recorded yet",
        )

    if pickup_request.assignment is None or pickup_request.assignment.weight_kg is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recorded weight is missing",
        )

    recorded_weight = pickup_request.assignment.weight_kg
    pickup_request.status = PickupStatus.completed
    pickup_request.assignment.completed_at = datetime.now(timezone.utc)
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.completed,
        f"Citizen confirmed the reported weight of {round(recorded_weight, 2)} kg.",
        actor=citizen,
    )
    _dispatcher.notify_weight_confirmed(db, pickup_request, recorded_weight)
    _record_audit(
        db,
        citizen,
        "pickup_weight_confirmed",
        pickup_request,
        after={"status": PickupStatus.completed.value, "weight_kg": recorded_weight},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=citizen)


def dispute_pickup_weight(
    db: Session, citizen: User, request_id: int, reason: str
) -> PickupRequestRead:
    """Citizen disputes the collector-reported weight (WIQ-V1-046).

    The pickup row is locked with ``SELECT ... FOR UPDATE`` before the
    state-machine check so that a concurrent confirm + dispute (or two
    disputes) cannot both observe ``status == weight_recorded`` and
    produce conflicting terminal states (WIQ-V1-053).

    The original collector measurement on ``assignment.weight_kg`` is
    preserved. A single ``pickup_disputes`` row records the dispute; the
    pickup enters the ``disputed`` state and waits for admin review.

    Idempotency: a second submission with the same reason returns the
    current state without creating a duplicate event/audit/notification.
    A different reason on an already-disputed pickup returns 409.
    A unique-constraint violation on ``pickup_disputes.request_id`` is
    caught and surfaced as 409 (covers the race where two disputes are
    submitted before either flushes the relationship).
    """
    pickup_request = _get_request_for_citizen_for_update(db, request_id, citizen)

    if pickup_request.status == PickupStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pickup is already completed and cannot be disputed",
        )

    if pickup_request.status == PickupStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancelled pickups cannot be disputed",
        )

    if pickup_request.status not in (
        PickupStatus.weight_recorded,
        PickupStatus.disputed,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Weight has not been recorded yet",
        )

    if pickup_request.assignment is None or pickup_request.assignment.weight_kg is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recorded weight is missing",
        )

    if pickup_request.dispute is not None:
        existing_reason = (pickup_request.dispute.reason or "").strip()
        new_reason = (reason or "").strip()
        if existing_reason == new_reason:
            return _to_schema(pickup_request, viewer=citizen)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dispute already exists for this pickup",
        )

    dispute = PickupDispute(request_id=pickup_request.id, reason=reason.strip())
    db.add(dispute)
    pickup_request.dispute = dispute
    pickup_request.status = PickupStatus.disputed
    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.disputed,
        "Citizen disputed the reported weight. Awaiting admin review.",
        actor=citizen,
    )
    _dispatcher.notify_weight_disputed(db, pickup_request)
    if pickup_request.assignment is not None:
        _dispatcher.notify_collector_dispute_filed(db, pickup_request)
    _record_audit(
        db,
        citizen,
        "pickup_weight_disputed",
        pickup_request,
        after={"status": PickupStatus.disputed.value},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dispute already exists for this pickup",
        ) from None
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=citizen)


def list_disputed_pickup_requests(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[PickupRequestRead], int]:
    """List pickups currently in the ``disputed`` state, newest first."""
    from sqlalchemy import func, select

    statement = _repository.base_query().where(PickupRequest.status == PickupStatus.disputed)
    total = db.execute(select(func.count()).select_from(statement.subquery())).scalar_one()

    items = (
        db.execute(
            statement.order_by(PickupRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .unique()
        .scalars()
        .all()
    )
    return [_to_schema(item, viewer=None) for item in items], int(total or 0)


def resolve_weight_dispute(
    db: Session,
    admin: User,
    request_id: int,
    payload: WeightDisputeResolveRequest,
) -> PickupRequestRead:
    """Admin resolves a weight dispute (WIQ-V1-046).

    The pickup row is locked with ``SELECT ... FOR UPDATE`` (WIQ-V1-053).
    This serialises concurrent resolution attempts and prevents a race where
    a citizen's confirm/dispute arrives while an admin is resolving.

    Outcomes:
      * ``upheld`` — accept the collector's original measurement, transition
        to ``completed``. The original ``assignment.weight_kg`` is preserved.
      * ``corrected`` — accept the dispute and set a corrected weight via
        ``dispute.resolved_weight_kg``. The original ``assignment.weight_kg``
        is preserved; the corrected value is stored on the dispute and on a
        snapshot ``completed_at`` audit record.
    """
    if admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can resolve disputes",
        )

    pickup_request = _repository.get_by_id_with_dispute_for_update(
        db, request_id, include_timeline=True
    )
    if pickup_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )

    if pickup_request.status != PickupStatus.disputed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pickup is not in a disputed state",
        )

    if pickup_request.dispute is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No dispute record found for this pickup",
        )

    if pickup_request.dispute.resolution is not None:
        return _to_schema(pickup_request, viewer=admin)

    resolution = DisputeResolution(payload.resolution)
    original_weight = pickup_request.assignment.weight_kg if pickup_request.assignment else None
    corrected_weight: float | None = None

    if resolution is DisputeResolution.upheld:
        if original_weight is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Original weight missing; cannot uphold",
            )
    else:
        if payload.resolved_weight_kg is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrected weight is required when resolution is 'corrected'",
            )
        corrected_weight = payload.resolved_weight_kg

    pickup_request.dispute.resolution = resolution
    pickup_request.dispute.resolved_at = datetime.now(timezone.utc)
    pickup_request.dispute.resolved_by_id = admin.id
    pickup_request.dispute.resolved_weight_kg = corrected_weight
    pickup_request.dispute.resolution_notes = payload.notes

    pickup_request.status = PickupStatus.completed
    if pickup_request.assignment is not None:
        pickup_request.assignment.completed_at = datetime.now(timezone.utc)

    _repository.add_status_event(
        db,
        pickup_request,
        PickupStatus.completed,
        (
            f"Admin upheld the collector weight of {round(original_weight or 0.0, 2)} kg."
            if resolution is DisputeResolution.upheld
            else f"Admin corrected the weight to {round(corrected_weight or 0.0, 2)} kg."
        ),
        actor=admin,
    )
    _dispatcher.notify_dispute_resolved(
        db,
        pickup_request,
        resolution.value,
        corrected_weight if corrected_weight is not None else original_weight,
    )
    _record_audit(
        db,
        admin,
        "pickup_dispute_resolved",
        pickup_request,
        after={
            "status": PickupStatus.completed.value,
            "resolution": resolution.value,
            "resolved_weight_kg": corrected_weight,
            "original_weight_kg": original_weight,
        },
    )
    _record_audit(
        db,
        admin,
        "pickup_dispute_reviewed",
        pickup_request,
        after={"status": PickupStatus.disputed.value},
    )
    db.commit()
    return _to_schema(_reload_pickup_or_500(db, pickup_request.id), viewer=admin)
