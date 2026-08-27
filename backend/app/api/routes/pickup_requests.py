from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_communication_service,
    get_current_user,
    get_db,
    get_image_uploader,
    get_pickup_request_creation_service,
    require_verified_roles,
    require_verified_user,
)
from app.models.user import User
from app.schemas.communication import ContactSessionRead
from app.schemas.pickup_request import (
    CitizenRequestSummaryRead,
    PickupRequestDetailRead,
    PickupRequestRead,
    PickupRequestUpdate,
)
from app.services.communication import CommunicationService
from app.services.pickup_requests import (
    cancel_pickup_request,
    get_citizen_request_summary,
    get_pickup_request_for_user,
    list_pickup_requests_for_user,
    update_pickup_request,
)
from app.services.pickup_request_creation import PickupRequestCreationService
from app.services.upload import ImageUploader

router = APIRouter()


@router.post("", response_model=PickupRequestRead, status_code=status.HTTP_201_CREATED)
def create_request(
    waste_type: str = Form(..., min_length=2, max_length=100),
    address: str = Form(..., min_length=8, max_length=500),
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    estimated_weight_kg: float | None = Form(default=None, ge=0, le=10000),
    preferred_time: datetime | None = Form(default=None),
    notes: str | None = Form(default=None, max_length=2000),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_roles("citizen")),
    creation_service: PickupRequestCreationService = Depends(get_pickup_request_creation_service),
) -> PickupRequestRead:
    return creation_service.create(
        db=db,
        citizen=current_user,
        waste_type=waste_type,
        address=address,
        latitude=latitude,
        longitude=longitude,
        estimated_weight_kg=estimated_weight_kg,
        preferred_time=preferred_time,
        notes=notes,
        image=image,
    )


@router.get("", response_model=list[PickupRequestRead])
def list_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PickupRequestRead]:
    return list_pickup_requests_for_user(db, current_user)


@router.get("/citizen/summary", response_model=CitizenRequestSummaryRead)
def citizen_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CitizenRequestSummaryRead:
    if current_user.role != "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only citizens can view dashboard metrics"
        )
    return get_citizen_request_summary(db, current_user)


@router.get("/{request_id}", response_model=PickupRequestDetailRead)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PickupRequestDetailRead:
    request = get_pickup_request_for_user(db, request_id, current_user)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    return request


@router.patch("/{request_id}", response_model=PickupRequestRead)
def patch_request(
    request_id: int,
    payload: PickupRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
) -> PickupRequestRead:
    request = update_pickup_request(db, request_id, current_user, payload)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    return request


@router.post("/{request_id}/cancel", response_model=PickupRequestRead)
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_roles("citizen")),
    uploader: ImageUploader = Depends(get_image_uploader),
) -> PickupRequestRead:
    request = cancel_pickup_request(db, current_user, request_id, uploader)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    return request


@router.post("/{request_id}/contact", response_model=ContactSessionRead)
def initiate_contact(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
    communication_service: CommunicationService = Depends(get_communication_service),
) -> ContactSessionRead:
    return communication_service.initiate_masked_contact(
        db=db, pickup_id=request_id, requester=current_user
    )
