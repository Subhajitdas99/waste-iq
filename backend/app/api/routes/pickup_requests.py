from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.pickup_request import PickupRequestCreate, PickupRequestRead, PickupRequestUpdate
from app.services.pickup_requests import (
    create_pickup_request,
    get_pickup_request_for_user,
    list_pickup_requests_for_user,
    update_pickup_request,
)

router = APIRouter()


@router.post("", response_model=PickupRequestRead, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: PickupRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PickupRequestRead:
    if current_user.role != "citizen":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only citizens can create requests")
    return create_pickup_request(db, current_user, payload)


@router.get("", response_model=list[PickupRequestRead])
def list_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PickupRequestRead]:
    return list_pickup_requests_for_user(db, current_user)


@router.get("/{request_id}", response_model=PickupRequestRead)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PickupRequestRead:
    request = get_pickup_request_for_user(db, request_id, current_user)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    return request


@router.patch("/{request_id}", response_model=PickupRequestRead)
def patch_request(
    request_id: int,
    payload: PickupRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PickupRequestRead:
    request = update_pickup_request(db, request_id, current_user, payload)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    return request
