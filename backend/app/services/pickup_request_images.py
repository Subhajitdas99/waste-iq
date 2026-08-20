import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.pickup_request import PickupRequest
from app.services.ai_classifier import AIClassifierProvider
from app.services.upload import ImageDeleteError, ImageUploader

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@dataclass(frozen=True)
class ProcessedPickupImage:
    image_url: str | None
    image_public_id: str | None
    category: str | None
    confidence: float | None


class PickupRequestImageService:
    def __init__(
        self,
        uploader: ImageUploader,
        classifier: AIClassifierProvider,
        upload_dir: str | Path = "uploads",
    ):
        self._uploader = uploader
        self._classifier = classifier
        self._upload_dir = Path(upload_dir)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def process_image(self, *, image: UploadFile | None, user_id: int) -> ProcessedPickupImage:
        if image is None or not image.filename:
            return ProcessedPickupImage(
                image_url=None, image_public_id=None, category=None, confidence=None
            )

        extension = self._get_extension(image.filename)
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format"
            )

        self._validate_size(image)
        temp_path = self._save_temp_file(image=image, extension=extension)
        category = "Unknown"
        confidence = 0.0

        try:
            try:
                ai_result = self._classifier.classify_image(str(temp_path))
                category = ai_result.get("category", "Unknown")
                confidence = ai_result.get("confidence", 0.0)
            except Exception:
                logger.warning(
                    "AI classification failed for pickup image.",
                    extra={"user_id": user_id, "image_filename": image.filename},
                )

            uploaded = self._uploader.upload_image(
                file_path=str(temp_path),
                filename=image.filename,
                user_id=user_id,
            )
            if uploaded is None:
                return ProcessedPickupImage(
                    image_url=None, image_public_id=None, category=None, confidence=None
                )

            return ProcessedPickupImage(
                image_url=uploaded.url,
                image_public_id=uploaded.public_id,
                category=category,
                confidence=confidence,
            )
        finally:
            self._cleanup_temp_file(temp_path=temp_path, user_id=user_id, filename=image.filename)

    def _validate_size(self, image: UploadFile) -> None:
        image.file.seek(0, os.SEEK_END)
        size = image.file.tell()
        image.file.seek(0)

        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Image size exceeds 10 MB limit"
            )

    def _save_temp_file(self, *, image: UploadFile, extension: str) -> Path:
        temp_path = self._upload_dir / f"{uuid.uuid4()}.{extension}"
        image.file.seek(0)
        with temp_path.open("wb") as file_handle:
            file_handle.write(image.file.read())
        image.file.seek(0)
        return temp_path

    def _cleanup_temp_file(self, *, temp_path: Path, user_id: int, filename: str) -> None:
        if not temp_path.exists():
            return

        try:
            temp_path.unlink()
        except OSError:
            logger.warning(
                "Failed to delete temporary pickup image.",
                extra={"user_id": user_id, "image_filename": filename},
            )

    @staticmethod
    def _get_extension(filename: str) -> str:
        return Path(filename).suffix.lower().lstrip(".")


def delete_uploaded_assets(uploader: ImageUploader, public_ids: list[str]) -> set[str]:
    """Best-effort provider-side deletion of multiple assets (WIQ-V1-020).

    Returns the set of public IDs confirmed gone (deleted, already deleted,
    or not found). Per-asset failures are logged and excluded from the result
    so callers can decide whether to drop their references. Deletion is
    idempotent: an already-missing asset counts as success.
    """
    deleted: set[str] = set()
    for public_id in public_ids:
        try:
            if uploader.delete_image(public_id=public_id):
                deleted.add(public_id)
        except ImageDeleteError:
            logger.warning(
                "Provider could not delete uploaded asset.",
                extra={"cloudinary_public_id": public_id},
            )
    return deleted


def cleanup_pickup_request_images(
    db: Session, pickup_request: PickupRequest, uploader: ImageUploader
) -> None:
    """Delete the pickup request's stored image assets on cancellation.

    Runs inside the caller's transaction: the status change and any reference
    cleanup commit together. If the provider confirms the asset is gone the
    database references are cleared so the DB never claims an asset exists
    after cleanup; if the provider is temporarily unavailable the references
    are kept (a future cleanup can retry) and the cancellation still proceeds.
    """
    public_id = pickup_request.image_public_id
    if not public_id:
        return
    if public_id in delete_uploaded_assets(uploader, [public_id]):
        pickup_request.image_url = None
        pickup_request.image_public_id = None
