import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.pickup_request import (
    CitizenRequestSummaryRead,
    PickupRequestCreate,
    PickupRequestDetailRead,
    PickupRequestRead,
    PickupRequestUpdate,
)
from app.services.pickup_requests import (
    cancel_pickup_request,
    create_pickup_request,
    get_citizen_request_summary,
    get_pickup_request_for_user,
    list_pickup_requests_for_user,
    update_pickup_request,
)
from app.services.cloudinary import upload_image_and_cleanup
from app.services.ai_classifier import get_classifier

router = APIRouter()

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("", response_model=PickupRequestRead, status_code=status.HTTP_201_CREATED)
def create_request(
    waste_type: str = Form(..., min_length=2, max_length=100),
    address: str = Form(..., min_length=8, max_length=500),
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PickupRequestRead:
    if current_user.role != "citizen":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only citizens can create requests")

    image_url = None
    category = None
    confidence = None
    if image is not None and image.filename:
        ext = image.filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format")
        
        image.file.seek(0, 2)
        size = image.file.tell()
        image.file.seek(0)
        
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image size exceeds 10 MB limit")
            
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image.file.read())
            
        category = "Unknown"
        confidence = 0.0
        try:
            ai_result = get_classifier().classify_image(filepath)
            category = ai_result.get("category", "Unknown")
            confidence = ai_result.get("confidence", 0.0)
        except Exception:
            pass
            
        secure_url = upload_image_and_cleanup(filepath)
        if not secure_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image")
        image_url = secure_url

    payload = PickupRequestCreate(
        waste_type=waste_type,
        address=address,
        latitude=latitude,
        longitude=longitude,
        image_url=image_url,
    )
    return create_pickup_request(
        db=db, 
        citizen=current_user, 
        payload=payload, 
        category=category if image_url else None,
        confidence=confidence if image_url else None
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only citizens can view dashboard metrics")
    return get_citizen_request_summary(db, current_user)


@router.get("/{request_id}", response_model=PickupRequestDetailRead)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PickupRequestDetailRead:
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


@router.post("/{request_id}/cancel", response_model=PickupRequestRead)
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PickupRequestRead:
    if current_user.role != "citizen":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only citizens can cancel requests")

    request = cancel_pickup_request(db, current_user, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    return request
