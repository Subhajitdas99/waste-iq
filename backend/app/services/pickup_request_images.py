import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.services.ai_classifier import AIClassifierProvider
from app.services.upload import ImageUploader

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@dataclass(frozen=True)
class ProcessedPickupImage:
    image_url: str | None
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
            return ProcessedPickupImage(image_url=None, category=None, confidence=None)

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

            image_url = self._uploader.upload_image(
                file_path=str(temp_path),
                filename=image.filename,
                user_id=user_id,
            )
            if image_url is None:
                return ProcessedPickupImage(image_url=None, category=None, confidence=None)

            return ProcessedPickupImage(
                image_url=image_url,
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
