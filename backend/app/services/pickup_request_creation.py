from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.pickup_request import PickupRequestCreate, PickupRequestRead
from app.services.pickup_request_images import PickupRequestImageService
from app.services.pickup_requests import create_pickup_request


class PickupRequestCreationService:
    def __init__(self, image_service: PickupRequestImageService):
        self._image_service = image_service

    def create(
        self,
        *,
        db: Session,
        citizen: User,
        waste_type: str,
        address: str,
        latitude: float,
        longitude: float,
        image: UploadFile | None,
    ) -> PickupRequestRead:
        processed_image = self._image_service.process_image(image=image, user_id=citizen.id)
        payload = PickupRequestCreate(
            waste_type=waste_type,
            address=address,
            latitude=latitude,
            longitude=longitude,
            image_url=processed_image.image_url,
        )
        return create_pickup_request(
            db=db,
            citizen=citizen,
            payload=payload,
            category=processed_image.category if processed_image.image_url else None,
            confidence=processed_image.confidence if processed_image.image_url else None,
        )
