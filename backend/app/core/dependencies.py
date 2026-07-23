from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(decode_access_token(credentials.credentials))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency


def get_ai_classifier():
    from app.services.ai_classifier import get_classifier

    return get_classifier()


def get_image_uploader(settings: Settings = Depends(get_settings)):
    from app.services.upload import CloudinaryUploadConfig, CloudinaryUploader

    return CloudinaryUploader(
        config=CloudinaryUploadConfig(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            required=settings.cloudinary_required,
        )
    )


def get_pickup_request_image_service(
    uploader=Depends(get_image_uploader),
    classifier=Depends(get_ai_classifier),
):
    from app.services.pickup_request_images import PickupRequestImageService

    return PickupRequestImageService(uploader=uploader, classifier=classifier)


def get_pickup_request_creation_service(
    image_service=Depends(get_pickup_request_image_service),
):
    from app.services.pickup_request_creation import PickupRequestCreationService

    return PickupRequestCreationService(image_service=image_service)
