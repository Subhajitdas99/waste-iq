from io import BytesIO

from app.core.config import get_settings

VALID_PICKUP_PAYLOAD = {
    "waste_type": "Plastic bottles",
    "address": "12 Lake Road, Kolkata, 700029",
    "latitude": 22.5726,
    "longitude": 88.3639,
}


def _override_settings(client, **updates):
    settings = get_settings().model_copy(update=updates)
    client.app.dependency_overrides[get_settings] = lambda: settings
    return settings


def _pickup_image(filename: str = "waste.png") -> dict[str, tuple[str, BytesIO, str]]:
    return {
        "image": (
            filename,
            BytesIO(b"fake-image-bytes"),
            "image/png",
        )
    }


def test_create_pickup_request_without_image_still_succeeds(client, citizen_headers):
    response = client.post("/pickup-requests", data=VALID_PICKUP_PAYLOAD, headers=citizen_headers)

    assert response.status_code == 201
    assert response.json()["image_url"] is None


def test_create_pickup_request_with_image_skips_upload_when_cloudinary_missing_in_development(
    client,
    citizen_headers,
):
    _override_settings(
        client,
        environment="development",
        cloudinary_cloud_name=None,
        cloudinary_api_key=None,
        cloudinary_api_secret=None,
    )

    response = client.post(
        "/pickup-requests",
        data=VALID_PICKUP_PAYLOAD,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["image_url"] is None
    assert body["category"] is None
    assert body["confidence"] is None


def test_create_pickup_request_with_image_returns_503_when_cloudinary_missing_in_production(
    client,
    citizen_headers,
):
    _override_settings(
        client,
        environment="production",
        cloudinary_cloud_name=None,
        cloudinary_api_key=None,
        cloudinary_api_secret=None,
    )

    response = client.post(
        "/pickup-requests",
        data=VALID_PICKUP_PAYLOAD,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Image upload service is not configured."}


def test_create_pickup_request_with_image_returns_502_when_cloudinary_upload_fails(
    client,
    citizen_headers,
    monkeypatch,
):
    _override_settings(
        client,
        environment="production",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="demo-secret",
    )

    def _raise_upload_error(_: str):
        raise RuntimeError("upstream failure")

    monkeypatch.setattr("app.services.upload.cloudinary.uploader.upload", _raise_upload_error)

    response = client.post(
        "/pickup-requests",
        data=VALID_PICKUP_PAYLOAD,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Image upload service unavailable."}


def test_create_pickup_request_with_image_uploads_successfully(
    client,
    citizen_headers,
    monkeypatch,
):
    _override_settings(
        client,
        environment="production",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="demo-secret",
    )

    def _upload_success(_: str):
        return {
            "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/pickups/waste.png",
            "public_id": "pickups/waste",
        }

    monkeypatch.setattr("app.services.upload.cloudinary.uploader.upload", _upload_success)

    response = client.post(
        "/pickup-requests",
        data=VALID_PICKUP_PAYLOAD,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["image_url"] == "https://res.cloudinary.com/demo/image/upload/v1/pickups/waste.png"
    assert body["category"] == "Unknown"
    assert body["confidence"] == 0.0
