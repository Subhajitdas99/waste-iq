from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.collector import CollectorCompleteRequest
from app.schemas.pickup_request import CollectorSummaryRead, NearbyPickupRequestRead, PickupRequestRead
from app.services.collector_summary import get_collector_summary
from app.services.pickup_requests import (
    accept_pickup_request,
    complete_pickup_request,
    list_assigned_pickup_requests_for_collector,
    list_available_pickup_requests_for_collector,
    list_nearby_pickup_requests_for_collector,
    mark_pickup_request_collected,
    mark_pickup_request_on_the_way,
)

router = APIRouter()


@router.get("/summary", response_model=CollectorSummaryRead)
def collector_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> CollectorSummaryRead:
    return get_collector_summary(db, current_user)


@router.get("/available", response_model=list[PickupRequestRead])
def available_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> list[PickupRequestRead]:
    return list_available_pickup_requests_for_collector(db)


@router.get("/nearby", response_model=list[NearbyPickupRequestRead])
def nearby_requests(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> list[NearbyPickupRequestRead]:
    return list_nearby_pickup_requests_for_collector(db, latitude, longitude, radius_km)


@router.get("/assigned", response_model=list[PickupRequestRead])
def assigned_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> list[PickupRequestRead]:
    return list_assigned_pickup_requests_for_collector(db, current_user)


@router.post("/accept/{request_id}", response_model=PickupRequestRead)
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> PickupRequestRead:
    return accept_pickup_request(db, current_user, request_id)


@router.post("/start/{request_id}", response_model=PickupRequestRead)
def start_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> PickupRequestRead:
    return mark_pickup_request_on_the_way(db, current_user, request_id)


@router.post("/collect/{request_id}", response_model=PickupRequestRead)
def collect_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> PickupRequestRead:
    return mark_pickup_request_collected(db, current_user, request_id)


@router.post("/complete/{request_id}", response_model=PickupRequestRead)
def complete_request(
    request_id: int,
    payload: CollectorCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> PickupRequestRead:
    return complete_pickup_request(db, current_user, request_id, payload.weight_kg)
