import logging
import uuid
from dataclasses import dataclass
from typing import Protocol

import cloudinary
import cloudinary.api
import cloudinary.uploader

logger = logging.getLogger(__name__)

# Standardized asset namespace (WIQ-V1-020): pickups/{user_id}/{uuid}.
# No email addresses, usernames, or other sensitive/identifying strings are
# ever used in storage paths.
UPLOAD_FOLDER_PREFIX = "pickups"


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


class ImageDeleteError(ImageUploadError):
    """Raised when a provider cannot delete an asset.

    A missing/already-deleted asset is NOT an error: deletion is idempotent
    and an absent asset is reported as successfully gone so cancellation
    cleanup never fails for that reason.
    """

    def __init__(self, detail: str = "Image deletion failed."):
        super().__init__(detail)


@dataclass(frozen=True)
class UploadedImage:
    """Provider-neutral result of an upload.

    ``public_id`` is the provider's stable identifier for the stored asset
    (e.g. the Cloudinary public_id or, for S3/R2, the object key). It is
    persisted by callers so cleanup can target the exact resource without
    reconstructing it from the URL.
    """

    url: str
    public_id: str


class ImageUploader(Protocol):
    def upload_image(
        self, *, file_path: str, filename: str, user_id: int | None = None
    ) -> UploadedImage | None: ...

    def delete_image(self, *, public_id: str) -> bool: ...


def build_public_id(*, user_id: int | None, filename: str) -> str:
    """Standardized per-user asset identifier (WIQ-V1-020).

    Format: ``pickups/{user_id}/{uuid4().hex}``. The random UUID guarantees
    uniqueness and opacity; the extension is intentionally omitted so the
    provider derives the format from the uploaded bytes.
    """
    namespace = f"{UPLOAD_FOLDER_PREFIX}/{user_id}" if user_id is not None else UPLOAD_FOLDER_PREFIX
    return f"{namespace}/{uuid.uuid4().hex}"


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
    ) -> UploadedImage | None:
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

        public_id = build_public_id(user_id=user_id, filename=filename)
        try:
            response = cloudinary.uploader.upload(file_path, public_id=public_id)
        except Exception:
            logger.exception(
                "Cloudinary upload failed.",
                extra={"user_id": user_id, "image_filename": filename},
            )
            raise ImageUploadUnavailableError() from None

        resolved_public_id = response.get("public_id") or public_id
        secure_url = response.get("secure_url")
        if not secure_url:
            logger.warning(
                "Cloudinary response did not include a secure URL.",
                extra={
                    "user_id": user_id,
                    "image_filename": filename,
                    "cloudinary_public_id": resolved_public_id,
                },
            )
            raise ImageUploadUnavailableError()

        logger.info(
            "Cloudinary upload succeeded.",
            extra={
                "user_id": user_id,
                "image_filename": filename,
                "cloudinary_public_id": resolved_public_id,
            },
        )
        return UploadedImage(url=secure_url, public_id=resolved_public_id)

    def delete_image(self, *, public_id: str) -> bool:
        """Delete the asset referenced by ``public_id`` (idempotent).

        Returns ``True`` when the asset is confirmed gone (deleted, already
        deleted, or not found). Raises :class:`ImageDeleteError` on genuine
        provider failures so callers can log and continue.
        """
        if not self._config.is_configured:
            if self._config.required:
                logger.warning(
                    "Cloudinary credentials are missing; cannot delete asset.",
                    extra={"cloudinary_public_id": public_id},
                )
                raise ImageDeleteError()
            logger.info(
                "Cloudinary credentials are missing; skipping asset deletion.",
                extra={"cloudinary_public_id": public_id},
            )
            return False

        try:
            response = cloudinary.api.delete_resources([public_id])
        except Exception:
            logger.exception(
                "Cloudinary asset deletion failed.",
                extra={"cloudinary_public_id": public_id},
            )
            raise ImageDeleteError() from None

        status = (response.get("deleted") or {}).get(public_id)
        if status in ("deleted", "already_deleted", "not_found"):
            return True
        if status is None:
            # Response did not mention the asset: do not assume it was removed.
            return False
        logger.warning(
            "Cloudinary reported unexpected deletion status.",
            extra={"cloudinary_public_id": public_id, "status": status},
        )
        return False
