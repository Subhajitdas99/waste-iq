from datetime import datetime, timedelta, timezone


def test_reservation_sets_expiry_24_hours_out(
    client, dealer_headers, approved_dealer_profile, inventory_lot
):
    response = client.post(
        f"/dealer/inventory-lots/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 200
    body = response.json()

    reserved_at = datetime.fromisoformat(body["reserved_at"].replace("Z", "+00:00"))
    expires_at = datetime.fromisoformat(body["reservation_expires_at"].replace("Z", "+00:00"))
    delta = expires_at - reserved_at
    assert timedelta(hours=23, minutes=55) < delta < timedelta(hours=24, minutes=5)


def test_expired_reservation_auto_released_on_list(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = approved_dealer_profile.user_id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    response = client.get("/dealer/inventory-lots", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    # Lot should now be available again and appear in the available listing.
    assert body["total_items"] == 1
    assert body["items"][0]["status"] == "available"


def test_expired_reservation_auto_released_on_detail_view(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = approved_dealer_profile.user_id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    response = client.get(f"/dealer/inventory-lots/{inventory_lot.id}", headers=dealer_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "available"


def test_expired_reservation_creates_reservation_expired_event(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session, admin_headers
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = approved_dealer_profile.user_id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    client.get("/dealer/inventory-lots", headers=dealer_headers)

    response = client.get(f"/admin/inventory-lots/{inventory_lot.id}/events", headers=admin_headers)
    events = response.json()
    event_types = [e["event_type"] for e in events]
    assert "reservation_expired" in event_types


def test_non_expired_reservation_not_released(
    client, dealer_headers, approved_dealer_profile, inventory_lot, db_session
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = approved_dealer_profile.user_id
    inventory_lot.reserved_at = datetime.now(timezone.utc)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) + timedelta(hours=23)
    db_session.commit()

    response = client.get("/dealer/inventory-lots", headers=dealer_headers)
    body = response.json()
    # Reserved-but-not-expired lots are excluded from the "available" listing entirely
    # (listing only shows status == available), so this should be empty, not error.
    assert body["total_items"] == 0


def test_release_expired_reservations_service_function_returns_count(
    db_session, inventory_lot, dealer_user
):
    from app.services.inventory_marketplace import release_expired_reservations
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = dealer_user.id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    released_count = release_expired_reservations(db_session)
    assert released_count == 1

    db_session.refresh(inventory_lot)
    assert inventory_lot.status == InventoryLotStatus.available
    assert inventory_lot.reserved_by_dealer_id is None
    assert inventory_lot.reserved_at is None
    assert inventory_lot.reservation_expires_at is None


def test_release_expired_reservations_with_nothing_to_release_returns_zero(
    db_session, inventory_lot
):
    from app.services.inventory_marketplace import release_expired_reservations

    # inventory_lot fixture is status=available by default, nothing reserved.
    released_count = release_expired_reservations(db_session)
    assert released_count == 0
