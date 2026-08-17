from typing import Any

VALID_PROFILE_PAYLOAD: dict[str, Any] = {
    "business_name": "Eco Scrap Traders",
    "owner_name": "Eco Owner",
    "phone": "9876543210",
    "email": "eco@scrap.in",
    "address": "12 Market Road, Howrah",
    "city": "Howrah",
    "state": "West Bengal",
    "postal_code": "711101",
    "gst_number": "19ABCDE1234F1Z5",
    "license_number": "WB-2026-00123",
    "materials_accepted": ["Metal", "Plastic"],
}


def _create_and_submit(client, dealer_headers, payload: dict[str, Any] | None = None):
    response = client.post(
        "/dealer/profile", json=payload or VALID_PROFILE_PAYLOAD, headers=dealer_headers
    )
    assert response.status_code == 201
    submit = client.post("/dealer/profile/submit", headers=dealer_headers)
    assert submit.status_code == 200
    return submit.json()


# ─── Duplicate identifiers ────────────────────────────────────────────────────


def test_duplicate_gst_number_rejected(client, dealer_headers, second_dealer_headers):
    _create_and_submit(client, dealer_headers)

    response = client.post(
        "/dealer/profile", json=VALID_PROFILE_PAYLOAD, headers=second_dealer_headers
    )
    assert response.status_code == 409


def test_duplicate_license_number_rejected(client, dealer_headers, second_dealer_headers):
    _create_and_submit(client, dealer_headers)

    duplicate_license_payload = {
        **VALID_PROFILE_PAYLOAD,
        "business_name": "Second Scrap Co",
        "gst_number": "29ABCDE1234F1Z1",
    }
    response = client.post(
        "/dealer/profile", json=duplicate_license_payload, headers=second_dealer_headers
    )
    assert response.status_code == 409


def test_gst_number_update_conflict_rejected(client, dealer_headers, second_dealer_headers):
    _create_and_submit(client, dealer_headers)

    second_payload = {
        **VALID_PROFILE_PAYLOAD,
        "business_name": "Second Scrap Co",
        "gst_number": "29ABCDE1234F1Z1",
        "license_number": "WB-2026-00099",
    }
    client.post("/dealer/profile", json=second_payload, headers=second_dealer_headers)

    response = client.put(
        "/dealer/profile", json={"gst_number": "29ABCDE1234F1Z1"}, headers=dealer_headers
    )
    assert response.status_code == 409


def test_same_dealer_can_keep_own_gst_number(client, dealer_headers):
    created = client.post("/dealer/profile", json=VALID_PROFILE_PAYLOAD, headers=dealer_headers)
    assert created.status_code == 201

    response = client.put(
        "/dealer/profile", json={"gst_number": "19ABCDE1234F1Z5"}, headers=dealer_headers
    )
    assert response.status_code == 200
    assert response.json()["gst_number"] == "19ABCDE1234F1Z5"


# ─── Invalid transitions ──────────────────────────────────────────────────────


def test_approve_draft_profile_is_rejected(client, dealer_headers, admin_headers, dealer_user):
    client.post("/dealer/profile", json=VALID_PROFILE_PAYLOAD, headers=dealer_headers)
    response = client.post(f"/admin/dealers/{dealer_user.id}/approve", headers=admin_headers)
    assert response.status_code == 400


def test_reject_draft_profile_is_rejected(client, dealer_headers, admin_headers, dealer_user):
    client.post("/dealer/profile", json=VALID_PROFILE_PAYLOAD, headers=dealer_headers)
    response = client.post(
        f"/admin/dealers/{dealer_user.id}/reject", json={"reason": "Nope"}, headers=admin_headers
    )
    assert response.status_code == 400


def test_approve_already_approved_profile_is_rejected(
    client, dealer_headers, admin_headers, dealer_user
):
    _create_and_submit(client, dealer_headers)
    approve = client.post(f"/admin/dealers/{dealer_user.id}/approve", headers=admin_headers)
    assert approve.status_code == 200

    response = client.post(f"/admin/dealers/{dealer_user.id}/approve", headers=admin_headers)
    assert response.status_code == 400


# ─── Admin review endpoints ───────────────────────────────────────────────────


def test_admin_approves_submitted_profile(client, dealer_headers, admin_headers, dealer_user):
    submitted = _create_and_submit(client, dealer_headers)
    profile_id = submitted["id"]

    response = client.post(f"/admin/dealers/{dealer_user.id}/approve", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["approval_status"] == "approved"
    assert body["profile_id"] == profile_id
    assert body["is_verified"] is True

    # Dealer now sees the approved status.
    profile = client.get("/dealer/profile", headers=dealer_headers)
    assert profile.json()["approval_status"] == "approved"


def test_admin_rejects_submitted_profile_with_reason(
    client, dealer_headers, admin_headers, dealer_user
):
    _create_and_submit(client, dealer_headers)

    response = client.post(
        f"/admin/dealers/{dealer_user.id}/reject",
        json={"reason": "Missing GST information"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["approval_status"] == "rejected"
    assert body["rejection_reason"] == "Missing GST information"

    profile = client.get("/dealer/profile", headers=dealer_headers)
    assert profile.json()["approval_status"] == "rejected"
    assert profile.json()["rejection_reason"] == "Missing GST information"


def test_reject_requires_reason(client, dealer_headers, admin_headers, dealer_user):
    _create_and_submit(client, dealer_headers)
    response = client.post(
        f"/admin/dealers/{dealer_user.id}/reject", json={}, headers=admin_headers
    )
    assert response.status_code == 422


def test_rejected_profile_can_resubmit(client, dealer_headers, admin_headers, dealer_user):
    _create_and_submit(client, dealer_headers)
    client.post(
        f"/admin/dealers/{dealer_user.id}/reject",
        json={"reason": "Fix address"},
        headers=admin_headers,
    )

    response = client.post("/dealer/profile/submit", headers=dealer_headers)
    assert response.status_code == 200
    assert response.json()["approval_status"] == "submitted"
    assert response.json()["rejection_reason"] is None


def test_admin_lists_dealers_with_pagination_and_filters(
    client, dealer_headers, admin_headers, second_dealer_headers, dealer_user
):
    _create_and_submit(client, dealer_headers)
    second_payload = {
        **VALID_PROFILE_PAYLOAD,
        "business_name": "Alpha Scrap Co",
        "gst_number": "29ABCDE1234F1Z1",
        "license_number": "WB-2026-00099",
    }
    client.post("/dealer/profile", json=second_payload, headers=second_dealer_headers)
    client.post("/dealer/profile/submit", headers=second_dealer_headers)
    client.post(f"/admin/dealers/{dealer_user.id}/approve", headers=admin_headers)

    page = client.get("/admin/dealers", headers=admin_headers)
    assert page.status_code == 200
    body = page.json()
    assert body["total_items"] == 2
    assert len(body["items"]) == 2

    filtered = client.get("/admin/dealers?status=submitted", headers=admin_headers)
    assert filtered.status_code == 200
    assert filtered.json()["total_items"] == 1
    assert filtered.json()["items"][0]["approval_status"] == "submitted"

    searched = client.get("/admin/dealers?search=Alpha", headers=admin_headers)
    assert searched.status_code == 200
    assert searched.json()["total_items"] == 1
    assert searched.json()["items"][0]["business_name"] == "Alpha Scrap Co"

    single = client.get("/admin/dealers?page=1&page_size=1", headers=admin_headers)
    assert single.json()["total_pages"] == 2
    assert len(single.json()["items"]) == 1


def test_admin_lists_pending_dealers(client, dealer_headers, admin_headers):
    _create_and_submit(client, dealer_headers)

    response = client.get("/admin/dealers/pending", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["approval_status"] == "submitted"
    assert body["items"][0]["business_name"] == "Eco Scrap Traders"


def test_admin_gets_dealer_detail_with_timeline(client, dealer_headers, admin_headers, dealer_user):
    _create_and_submit(client, dealer_headers)
    client.post(
        f"/admin/dealers/{dealer_user.id}/reject",
        json={"reason": "Bad license"},
        headers=admin_headers,
    )
    client.post("/dealer/profile/submit", headers=dealer_headers)
    client.post(f"/admin/dealers/{dealer_user.id}/approve", headers=admin_headers)

    response = client.get(f"/admin/dealers/{dealer_user.id}", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["user_name"] == "Test User"
    assert body["profile"]["approval_status"] == "approved"
    assert body["profile"]["profile_completion"] == 100

    statuses = [event["status"] for event in body["timeline"]]
    assert statuses == ["approved", "submitted", "rejected", "submitted", "draft"]
    assert body["timeline"][0]["actor_role"] == "admin"


def test_admin_get_nonexistent_dealer_returns_404(client, admin_headers):
    response = client.get("/admin/dealers/999999", headers=admin_headers)
    assert response.status_code == 404


# ─── Permissions ──────────────────────────────────────────────────────────────


def test_dealer_cannot_approve_profile(client, dealer_headers, admin_headers, dealer_user):
    _create_and_submit(client, dealer_headers)

    response = client.post(f"/admin/dealers/{dealer_user.id}/approve", headers=dealer_headers)
    assert response.status_code == 403


def test_admin_cannot_create_dealer_profile(client, admin_headers):
    response = client.post("/dealer/profile", json=VALID_PROFILE_PAYLOAD, headers=admin_headers)
    assert response.status_code == 403


def test_admin_cannot_submit_dealer_profile(client, admin_headers):
    response = client.post("/dealer/profile/submit", headers=admin_headers)
    assert response.status_code == 403


def test_anonymous_cannot_access_admin_dealer_routes(client):
    assert client.get("/admin/dealers").status_code == 401
    assert client.get("/admin/dealers/pending").status_code == 401
    assert client.post("/admin/dealers/3/approve").status_code == 401
    assert client.post("/admin/dealers/3/reject", json={"reason": "x"}).status_code == 401
