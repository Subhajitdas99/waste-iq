from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.user import User
from app.schemas.collector import CollectorCompleteRequest
from app.schemas.pickup_request import PickupRequestRead
from app.services.pickup_requests import accept_pickup_request, complete_pickup_request

router = APIRouter()


@router.post("/accept/{request_id}", response_model=PickupRequestRead)
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> PickupRequestRead:
    return accept_pickup_request(db, current_user, request_id)


@router.post("/complete/{request_id}", response_model=PickupRequestRead)
def complete_request(
    request_id: int,
    payload: CollectorCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> PickupRequestRead:
    return complete_pickup_request(db, current_user, request_id, payload.weight_kg)
