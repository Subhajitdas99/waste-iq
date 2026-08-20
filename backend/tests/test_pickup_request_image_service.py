from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.services.ai_classifier import AIClassifierProvider
from app.services.pickup_request_images import (
    PickupRequestImageService,
    cleanup_pickup_request_images,
    delete_uploaded_assets,
)
from app.services.upload import (
    CloudinaryUploadConfig,
    CloudinaryUploader,
    ImageDeleteError,
    ImageUploader,
    ImageUploadUnavailableError,
    UploadedImage,
    build_public_id,
)


class StubClassifier(AIClassifierProvider):
    def classify_image(self, image_path: str) -> dict[str, object]:
        return {
            "category": "Plastic",
            "confidence": 0.91,
            "detections": [],
        }


class StubUploader(ImageUploader):
    def __init__(
        self,
        result: UploadedImage | None = None,
        error: Exception | None = None,
        delete_results: dict[str, bool] | None = None,
        delete_errors: dict[str, Exception] | None = None,
    ):
        self._result = result
        self._error = error
        self._delete_results = delete_results or {}
        self._delete_errors = delete_errors or {}
        self.deleted_public_ids: list[str] = []

    def upload_image(
        self, *, file_path: str, filename: str, user_id: int | None = None
    ) -> UploadedImage | None:
        if self._error is not None:
            raise self._error
        return self._result

    def delete_image(self, *, public_id: str) -> bool:
        self.deleted_public_ids.append(public_id)
        if public_id in self._delete_errors:
            raise self._delete_errors[public_id]
        return self._delete_results.get(public_id, True)


def _upload_file(name: str = "waste.png") -> UploadFile:
    return UploadFile(filename=name, file=BytesIO(b"fake-image-bytes"))


def _fake_pickup_request(**overrides):
    class _FakePickup:
        pass

    request = _FakePickup()
    request.image_url = "https://res.cloudinary.com/demo/image/upload/v1/pickups/waste.png"
    request.image_public_id = "pickups/1/abc123"
    for key, value in overrides.items():
        setattr(request, key, value)
    return request


def test_pickup_request_image_service_cleans_temp_file_after_success(tmp_path):
    service = PickupRequestImageService(
        uploader=StubUploader(
            result=UploadedImage(url="https://example.com/image.png", public_id="pickups/1/abc123")
        ),
        classifier=StubClassifier(),
        upload_dir=tmp_path,
    )

    result = service.process_image(image=_upload_file(), user_id=1)

    assert result.image_url == "https://example.com/image.png"
    assert result.image_public_id == "pickups/1/abc123"
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


def test_pickup_request_image_service_returns_none_when_uploader_skips(tmp_path):
    service = PickupRequestImageService(
        uploader=StubUploader(result=None),
        classifier=StubClassifier(),
        upload_dir=tmp_path,
    )

    result = service.process_image(image=_upload_file(), user_id=1)

    assert result.image_url is None
    assert result.image_public_id is None
    assert result.category is None
    assert result.confidence is None


def test_pickup_request_image_service_rejects_unsupported_file_type(tmp_path):
    service = PickupRequestImageService(
        uploader=StubUploader(),
        classifier=StubClassifier(),
        upload_dir=tmp_path,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.process_image(image=_upload_file(name="waste.gif"), user_id=1)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid image format"
    assert list(tmp_path.iterdir()) == []


def test_pickup_request_image_service_rejects_oversized_file(tmp_path):
    service = PickupRequestImageService(
        uploader=StubUploader(),
        classifier=StubClassifier(),
        upload_dir=tmp_path,
    )

    oversized = UploadFile(filename="waste.png", file=BytesIO(b"x" * (10 * 1024 * 1024 + 1)))

    with pytest.raises(HTTPException) as exc_info:
        service.process_image(image=oversized, user_id=1)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Image size exceeds 10 MB limit"
    assert list(tmp_path.iterdir()) == []


def test_delete_uploaded_assets_deletes_multiple_assets_and_reports_failures():
    uploader = StubUploader(
        delete_results={
            "pickups/1/a": True,
            "pickups/1/c": True,
        },
        delete_errors={"pickups/1/b": ImageDeleteError()},
    )

    deleted = delete_uploaded_assets(uploader, ["pickups/1/a", "pickups/1/b", "pickups/1/c"])

    assert deleted == {"pickups/1/a", "pickups/1/c"}
    assert uploader.deleted_public_ids == ["pickups/1/a", "pickups/1/b", "pickups/1/c"]


def test_cleanup_pickup_request_images_clears_references_on_success():
    uploader = StubUploader(delete_results={"pickups/1/abc123": True})
    request = _fake_pickup_request()

    cleanup_pickup_request_images(db=None, pickup_request=request, uploader=uploader)

    assert uploader.deleted_public_ids == ["pickups/1/abc123"]
    assert request.image_url is None
    assert request.image_public_id is None


def test_cleanup_pickup_request_images_treats_missing_asset_as_gone():
    uploader = StubUploader(delete_results={"pickups/1/abc123": True})
    request = _fake_pickup_request()

    cleanup_pickup_request_images(db=None, pickup_request=request, uploader=uploader)

    assert uploader.deleted_public_ids == ["pickups/1/abc123"]
    assert request.image_url is None
    assert request.image_public_id is None


def test_cleanup_pickup_request_images_keeps_reference_when_delete_fails():
    uploader = StubUploader(delete_errors={"pickups/1/abc123": ImageDeleteError()})
    request = _fake_pickup_request()

    cleanup_pickup_request_images(db=None, pickup_request=request, uploader=uploader)

    assert uploader.deleted_public_ids == ["pickups/1/abc123"]
    assert request.image_url is not None
    assert request.image_public_id == "pickups/1/abc123"


def test_cleanup_pickup_request_images_is_noop_without_public_id():
    uploader = StubUploader()
    request = _fake_pickup_request(image_public_id=None)

    cleanup_pickup_request_images(db=None, pickup_request=request, uploader=uploader)

    assert uploader.deleted_public_ids == []
    assert request.image_url is not None
    assert request.image_public_id is None


# ─── CloudinaryUploader unit tests ─────────────────────────────────────────────


def _configured_uploader():
    return CloudinaryUploader(
        config=CloudinaryUploadConfig(
            cloud_name="demo-cloud",
            api_key="demo-key",
            api_secret="demo-secret",
            required=True,
        )
    )


def test_build_public_id_uses_per_user_folder_and_standardized_uuid():
    public_id = build_public_id(user_id=123, filename="waste.png")

    assert public_id.startswith("pickups/123/")
    suffix = public_id.split("/")[-1]
    assert len(suffix) == 32
    assert all(c in "0123456789abcdef" for c in suffix)
    assert ".png" not in public_id


def test_build_public_id_omits_user_when_absent():
    public_id = build_public_id(user_id=None, filename="waste.png")

    assert public_id.startswith("pickups/")
    assert len(public_id.split("/")) == 2


def test_cloudinary_upload_uses_per_user_public_id(monkeypatch):
    captured = {}
    monkeypatch.setattr("app.services.upload.cloudinary.config", lambda **kwargs: None)

    def _upload(_: str, **kwargs):
        captured.update(kwargs)
        return {
            "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/x.png",
            "public_id": kwargs["public_id"],
        }

    monkeypatch.setattr("app.services.upload.cloudinary.uploader.upload", _upload)

    uploader = _configured_uploader()
    result = uploader.upload_image(file_path="tmp.png", filename="waste.png", user_id=7)

    assert captured["public_id"].startswith("pickups/7/")
    assert result is not None
    assert result.public_id == captured["public_id"]
    assert result.url == "https://res.cloudinary.com/demo/image/upload/v1/x.png"


def test_cloudinary_delete_returns_true_for_deleted_and_not_found(monkeypatch):
    uploader = _configured_uploader()

    monkeypatch.setattr(
        "app.services.upload.cloudinary.api.delete_resources",
        lambda public_ids, **kwargs: {"deleted": {"pickups/1/a": "deleted"}},
    )
    assert uploader.delete_image(public_id="pickups/1/a") is True

    monkeypatch.setattr(
        "app.services.upload.cloudinary.api.delete_resources",
        lambda public_ids, **kwargs: {"deleted": {"pickups/1/a": "not_found"}},
    )
    assert uploader.delete_image(public_id="pickups/1/a") is True

    monkeypatch.setattr(
        "app.services.upload.cloudinary.api.delete_resources",
        lambda public_ids, **kwargs: {"deleted": {"pickups/1/a": "already_deleted"}},
    )
    assert uploader.delete_image(public_id="pickups/1/a") is True


def test_cloudinary_delete_returns_false_for_unexpected_status(monkeypatch):
    uploader = _configured_uploader()

    monkeypatch.setattr(
        "app.services.upload.cloudinary.api.delete_resources",
        lambda public_ids, **kwargs: {"deleted": {"pickups/1/a": "processing"}},
    )
    assert uploader.delete_image(public_id="pickups/1/a") is False

    monkeypatch.setattr(
        "app.services.upload.cloudinary.api.delete_resources",
        lambda public_ids, **kwargs: {"deleted": {}},
    )
    assert uploader.delete_image(public_id="pickups/1/a") is False


def test_cloudinary_delete_raises_on_provider_error(monkeypatch):
    uploader = _configured_uploader()

    def _boom(public_ids, **kwargs):
        raise RuntimeError("upstream failure")

    monkeypatch.setattr("app.services.upload.cloudinary.api.delete_resources", _boom)

    with pytest.raises(ImageDeleteError):
        uploader.delete_image(public_id="pickups/1/a")
