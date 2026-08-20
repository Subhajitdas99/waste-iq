from io import BytesIO

from app.core.config import get_settings
from app.models.pickup_request import PickupRequest


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


def _production_cloudinary_settings(client):
    return _override_settings(
        client,
        environment="production",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="demo-secret",
    )


def test_create_pickup_request_without_image_still_succeeds(
    client, citizen_headers, valid_pickup_payload
):
    response = client.post("/pickup-requests", data=valid_pickup_payload, headers=citizen_headers)

    assert response.status_code == 201
    assert response.json()["image_url"] is None


def test_create_pickup_request_with_image_skips_upload_when_cloudinary_missing_in_development(
    client,
    citizen_headers,
    valid_pickup_payload,
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
        data=valid_pickup_payload,
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
    valid_pickup_payload,
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
        data=valid_pickup_payload,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Image upload service is not configured."}


def test_production_configuration_error_does_not_leak_credentials(
    client,
    citizen_headers,
    valid_pickup_payload,
):
    _override_settings(
        client,
        environment="production",
        cloudinary_cloud_name=None,
        cloudinary_api_key="super-secret-key-123",
        cloudinary_api_secret="super-secret-secret-456",
    )

    response = client.post(
        "/pickup-requests",
        data=valid_pickup_payload,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 503
    body_text = response.text
    assert "super-secret-key-123" not in body_text
    assert "super-secret-secret-456" not in body_text
    assert response.json() == {"detail": "Image upload service is not configured."}


def test_create_pickup_request_with_image_returns_502_when_cloudinary_upload_fails(
    client,
    citizen_headers,
    monkeypatch,
    valid_pickup_payload,
):
    _production_cloudinary_settings(client)

    def _raise_upload_error(_: str, **kwargs):
        raise RuntimeError("upstream failure")

    monkeypatch.setattr("app.services.upload.cloudinary.uploader.upload", _raise_upload_error)

    response = client.post(
        "/pickup-requests",
        data=valid_pickup_payload,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Image upload service unavailable."}


def test_create_pickup_request_with_image_uploads_to_per_user_folder(
    client,
    db_session,
    citizen_user,
    citizen_headers,
    monkeypatch,
    valid_pickup_payload,
):
    _production_cloudinary_settings(client)

    captured = {}

    def _upload_success(_: str, **kwargs):
        captured["public_id"] = kwargs["public_id"]
        return {
            "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/x.png",
            "public_id": kwargs["public_id"],
        }

    monkeypatch.setattr("app.services.upload.cloudinary.uploader.upload", _upload_success)

    response = client.post(
        "/pickup-requests",
        data=valid_pickup_payload,
        files=_pickup_image(),
        headers=citizen_headers,
    )

    assert response.status_code == 201
    prefix = f"pickups/{citizen_user.id}/"
    assert captured["public_id"].startswith(prefix)
    suffix = captured["public_id"][len(prefix) :]
    assert len(suffix) == 32
    assert all(c in "0123456789abcdef" for c in suffix)

    persisted = db_session.get(PickupRequest, response.json()["id"])
    assert persisted is not None
    assert persisted.image_public_id == captured["public_id"]
    assert persisted.image_url is not None


def test_create_pickup_request_rejects_unsupported_image_type(
    client,
    citizen_headers,
    valid_pickup_payload,
):
    _production_cloudinary_settings(client)

    response = client.post(
        "/pickup-requests",
        data=valid_pickup_payload,
        files=_pickup_image(filename="waste.gif"),
        headers=citizen_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image format"


def _create_pickup_with_image(client, citizen_headers, valid_pickup_payload, monkeypatch):
    captured = []

    def _upload_success(_: str, **kwargs):
        captured.append(kwargs["public_id"])
        return {
            "secure_url": f"https://res.cloudinary.com/demo/image/upload/v1/{kwargs['public_id']}.png",
            "public_id": kwargs["public_id"],
        }

    monkeypatch.setattr("app.services.upload.cloudinary.uploader.upload", _upload_success)

    created = client.post(
        "/pickup-requests",
        data=valid_pickup_payload,
        files=_pickup_image(),
        headers=citizen_headers,
    ).json()
    return created, captured[0]


def test_cancel_pickup_request_deletes_cloudinary_asset(
    client,
    db_session,
    citizen_headers,
    monkeypatch,
    valid_pickup_payload,
):
    _production_cloudinary_settings(client)
    created, public_id = _create_pickup_with_image(
        client, citizen_headers, valid_pickup_payload, monkeypatch
    )
    assert public_id.startswith("pickups/")

    deleted = []

    def _delete_resources(public_ids, **kwargs):
        deleted.extend(public_ids)
        return {"deleted": {pid: "deleted" for pid in public_ids}}

    monkeypatch.setattr("app.services.upload.cloudinary.api.delete_resources", _delete_resources)

    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=citizen_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert deleted == [public_id]

    persisted = db_session.get(PickupRequest, created["id"])
    assert persisted.image_url is None
    assert persisted.image_public_id is None


def test_cancel_pickup_request_succeeds_when_asset_already_missing(
    client,
    db_session,
    citizen_headers,
    monkeypatch,
    valid_pickup_payload,
):
    _production_cloudinary_settings(client)
    created, public_id = _create_pickup_with_image(
        client, citizen_headers, valid_pickup_payload, monkeypatch
    )

    def _delete_resources(public_ids, **kwargs):
        return {"deleted": {pid: "not_found" for pid in public_ids}}

    monkeypatch.setattr("app.services.upload.cloudinary.api.delete_resources", _delete_resources)

    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=citizen_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    persisted = db_session.get(PickupRequest, created["id"])
    assert persisted.image_url is None
    assert persisted.image_public_id is None


def test_cancel_pickup_request_succeeds_when_delete_fails(
    client,
    db_session,
    citizen_headers,
    monkeypatch,
    valid_pickup_payload,
):
    _production_cloudinary_settings(client)
    created, public_id = _create_pickup_with_image(
        client, citizen_headers, valid_pickup_payload, monkeypatch
    )

    def _delete_resources(public_ids, **kwargs):
        raise RuntimeError("upstream failure")

    monkeypatch.setattr("app.services.upload.cloudinary.api.delete_resources", _delete_resources)

    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=citizen_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    # Reference is kept on transient failure so a later cleanup can retry.
    persisted = db_session.get(PickupRequest, created["id"])
    assert persisted.image_url is not None
    assert persisted.image_public_id == public_id


def test_cancel_pickup_request_without_image_does_not_call_delete(
    client,
    db_session,
    citizen_headers,
    monkeypatch,
    valid_pickup_payload,
):
    _production_cloudinary_settings(client)
    created = client.post(
        "/pickup-requests", data=valid_pickup_payload, headers=citizen_headers
    ).json()

    deleted = []

    def _delete_resources(public_ids, **kwargs):
        deleted.extend(public_ids)
        return {"deleted": {pid: "deleted" for pid in public_ids}}

    monkeypatch.setattr("app.services.upload.cloudinary.api.delete_resources", _delete_resources)

    response = client.post(f"/pickup-requests/{created['id']}/cancel", headers=citizen_headers)

    assert response.status_code == 200
    assert deleted == []

    persisted = db_session.get(PickupRequest, created["id"])
    assert persisted.image_url is None
    assert persisted.image_public_id is None
