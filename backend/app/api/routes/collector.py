from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.collector import CollectorCompleteRequest
from app.schemas.pickup_request import CollectorSummaryRead, PickupRequestRead
from app.services.collector_summary import get_collector_summary
from app.services.pickup_requests import (
    accept_pickup_request,
    complete_pickup_request,
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