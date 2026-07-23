from io import BytesIO

import pytest
from fastapi import UploadFile

from app.services.ai_classifier import AIClassifierProvider
from app.services.pickup_request_images import PickupRequestImageService
from app.services.upload import ImageUploadUnavailableError, ImageUploader


class StubClassifier(AIClassifierProvider):
    def classify_image(self, image_path: str) -> dict[str, object]:
        return {
            "category": "Plastic",
            "confidence": 0.91,
            "detections": [],
        }


class StubUploader(ImageUploader):
    def __init__(self, result: str | None = None, error: Exception | None = None):
        self._result = result
        self._error = error

    def upload_image(
        self, *, file_path: str, filename: str, user_id: int | None = None
    ) -> str | None:
        if self._error is not None:
            raise self._error
        return self._result


def _upload_file(name: str = "waste.png") -> UploadFile:
    return UploadFile(filename=name, file=BytesIO(b"fake-image-bytes"))


def test_pickup_request_image_service_cleans_temp_file_after_success(tmp_path):
    service = PickupRequestImageService(
        uploader=StubUploader(result="https://example.com/image.png"),
        classifier=StubClassifier(),
        upload_dir=tmp_path,
    )

    result = service.process_image(image=_upload_file(), user_id=1)

    assert result.image_url == "https://example.com/image.png"
    assert list(tmp_path.iterdir()) == []


def test_pickup_request_image_service_cleans_temp_file_after_upload_failure(tmp_path):
    service = PickupRequestImageService(
        uploader=StubUploader(error=ImageUploadUnavailableError()),
        classifier=StubClassifier(),
        upload_dir=tmp_path,
    )

    with pytest.raises(ImageUploadUnavailableError):
        service.process_image(image=_upload_file(), user_id=1)

    assert list(tmp_path.iterdir()) == []
