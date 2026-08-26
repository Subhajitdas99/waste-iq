from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.core.sentry_sdk import set_sentry_user
from app.db.session import SessionLocal
from app.models.user import User
from app.services.ai_classifier import AIClassifierProvider, get_classifier
from app.services.pickup_request_creation import PickupRequestCreationService
from app.services.pickup_request_images import PickupRequestImageService
from app.services.upload import CloudinaryUploadConfig, CloudinaryUploader

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

    # Correlate Sentry errors with the authenticated account (id only).
    set_sentry_user(user.id)
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency


def require_verified_user(user: User = Depends(get_current_user)) -> User:
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required"
        )
    return user


def require_verified_roles(*roles: str):
    def dependency(user: User = Depends(require_verified_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency


def get_ai_classifier() -> AIClassifierProvider:
    return get_classifier()


def get_image_uploader(settings: Settings = Depends(get_settings)) -> CloudinaryUploader:
    return CloudinaryUploader(
        config=CloudinaryUploadConfig(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            required=settings.cloudinary_required,
        )
    )


def get_pickup_request_image_service(
    uploader: CloudinaryUploader = Depends(get_image_uploader),
    classifier: AIClassifierProvider = Depends(get_ai_classifier),
) -> PickupRequestImageService:
    return PickupRequestImageService(uploader=uploader, classifier=classifier)


def get_pickup_request_creation_service(
    image_service: PickupRequestImageService = Depends(get_pickup_request_image_service),
) -> PickupRequestCreationService:
    return PickupRequestCreationService(image_service=image_service)
