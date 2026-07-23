import logging
from dataclasses import dataclass

import cloudinary
import cloudinary.uploader
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CloudinaryUploadConfig:
    cloud_name: str | None
    api_key: str | None
    api_secret: str | None
    required: bool = False

    @property
    def is_configured(self) -> bool:
        return all([self.cloud_name, self.api_key, self.api_secret])


class ImageUploadError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class ImageUploadConfigurationError(ImageUploadError):
    def __init__(self, detail: str = "Image upload service is not configured."):
        super().__init__(detail)


class ImageUploadUnavailableError(ImageUploadError):
    def __init__(self, detail: str = "Image upload service unavailable."):
        super().__init__(detail)


class ImageUploader(Protocol):
    def upload_image(
        self, *, file_path: str, filename: str, user_id: int | None = None
    ) -> str | None: ...


class CloudinaryUploader:
    def __init__(self, config: CloudinaryUploadConfig):
        self._config = config
        if self._config.is_configured:
            cloudinary.config(
                cloud_name=self._config.cloud_name,
                api_key=self._config.api_key,
                api_secret=self._config.api_secret,
            )

    def upload_image(
        self, *, file_path: str, filename: str, user_id: int | None = None
    ) -> str | None:
        if not self._config.is_configured:
            if self._config.required:
                logger.warning(
                    "Cloudinary credentials are missing for a required upload.",
                    extra={"user_id": user_id, "image_filename": filename},
                )
                raise ImageUploadConfigurationError()

            logger.info(
                "Cloudinary credentials are missing; skipping optional upload.",
                extra={"user_id": user_id, "image_filename": filename},
            )
            return None

        try:
            response = cloudinary.uploader.upload(file_path)
        except Exception:
            logger.exception(
                "Cloudinary upload failed.",
                extra={"user_id": user_id, "image_filename": filename},
            )
            raise ImageUploadUnavailableError() from None

        public_id = response.get("public_id")
        secure_url = response.get("secure_url")
        if not secure_url:
            logger.warning(
                "Cloudinary response did not include a secure URL.",
                extra={
                    "user_id": user_id,
                    "image_filename": filename,
                    "cloudinary_public_id": public_id,
                },
            )
            raise ImageUploadUnavailableError()

        logger.info(
            "Cloudinary upload succeeded.",
            extra={
                "user_id": user_id,
                "image_filename": filename,
                "cloudinary_public_id": public_id,
            },
        )
        return secure_url
