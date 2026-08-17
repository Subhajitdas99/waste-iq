from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dealer_inventory import DealerInventory, DealerInventoryStatus
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User


def test_create_dealer_inventory(
    client: TestClient,
    db_session: Session,
    dealer_user: User,
    dealer_headers: dict,
    approved_dealer_profile,
) -> None:
    # First create a completed pickup request
    pickup = PickupRequest(
        user_id=1,
        waste_type="Plastic",
        status=PickupStatus.completed,
        latitude=0.0,
        longitude=0.0,
        address="123 Test St",
    )
    db_session.add(pickup)
    db_session.commit()

    payload = {
        "pickup_request_id": pickup.id,
        "material_type": "Aluminum",
        "category": "Metal",
        "quantity_kg": 5.5,
        "price_per_kg": 2.0,
        "quality_grade": "A",
    }

    response = client.post("/dealer/inventory", headers=dealer_headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["pickup_request_id"] == pickup.id
    assert data["material_type"] == "Aluminum"
    assert data["total_value"] == "11.00"
    assert data["status"] == "available"


def test_create_inventory_invalid_pickup(
    client: TestClient,
    db_session: Session,
    dealer_user: User,
    dealer_headers: dict,
    approved_dealer_profile,
) -> None:
    pickup = PickupRequest(
        user_id=1,
        waste_type="Plastic",
        status=PickupStatus.pending,  # Not completed
        latitude=0.0,
        longitude=0.0,
        address="123 Test St",
    )
    db_session.add(pickup)
    db_session.commit()

    payload = {
        "pickup_request_id": pickup.id,
        "material_type": "Aluminum",
        "category": "Metal",
        "quantity_kg": 5.5,
        "price_per_kg": 2.0,
    }

    response = client.post("/dealer/inventory", headers=dealer_headers, json=payload)
    assert response.status_code == 400


def test_list_and_update_inventory(
    client: TestClient,
    db_session: Session,
    dealer_user: User,
    dealer_headers: dict,
    approved_dealer_profile,
) -> None:
    pickup = PickupRequest(
        user_id=1,
        waste_type="Plastic",
        status=PickupStatus.completed,
        latitude=0.0,
        longitude=0.0,
        address="123 Test St",
    )
    db_session.add(pickup)
    db_session.commit()

    inv = DealerInventory(
        dealer_id=dealer_user.id,
        pickup_request_id=pickup.id,
        material_type="Plastic",
        category="Plastic",
        quantity_kg=10.0,
        price_per_kg=Decimal("1.50"),
        total_value=Decimal("15.00"),
        status=DealerInventoryStatus.available,
    )
    db_session.add(inv)
    db_session.commit()

    # List
    res = client.get("/dealer/inventory", headers=dealer_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 1

    # Update
    update_payload = {"price_per_kg": 3.0}
    res2 = client.put(f"/dealer/inventory/{inv.id}", headers=dealer_headers, json=update_payload)
    assert res2.status_code == 200
    assert res2.json()["total_value"] == "30.00"


def test_inventory_lifecycle(
    client: TestClient,
    db_session: Session,
    dealer_user: User,
    dealer_headers: dict,
    approved_dealer_profile,
) -> None:
    pickup = PickupRequest(
        user_id=1,
        waste_type="Plastic",
        status=PickupStatus.completed,
        latitude=0.0,
        longitude=0.0,
        address="123 Test St",
    )
    db_session.add(pickup)
    db_session.commit()

    inv = DealerInventory(
        dealer_id=dealer_user.id,
        pickup_request_id=pickup.id,
        material_type="Glass",
        category="Glass",
        quantity_kg=5.0,
        price_per_kg=Decimal("1.00"),
        total_value=Decimal("5.00"),
        status=DealerInventoryStatus.available,
    )
    db_session.add(inv)
    db_session.commit()

    # Reserve
    res = client.post(f"/dealer/inventory/{inv.id}/reserve", headers=dealer_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "reserved"

    # Release
    res = client.post(f"/dealer/inventory/{inv.id}/release", headers=dealer_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "available"

    # Mark Sold
    res = client.post(f"/dealer/inventory/{inv.id}/mark-sold", headers=dealer_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "sold"

    # Try to delete sold
    res = client.delete(f"/dealer/inventory/{inv.id}", headers=dealer_headers)
    assert res.status_code == 400


# ─── Approval gate ────────────────────────────────────────────────────────────


def test_unapproved_dealer_cannot_list_inventory(client, dealer_headers, submitted_dealer_profile):
    res = client.get("/dealer/inventory", headers=dealer_headers)
    assert res.status_code == 403


def test_dealer_without_profile_cannot_create_inventory(client, dealer_headers):
    res = client.post(
        "/dealer/inventory",
        headers=dealer_headers,
        json={
            "pickup_request_id": 1,
            "material_type": "Aluminum",
            "category": "Metal",
            "quantity_kg": 5.5,
            "price_per_kg": 2.0,
        },
    )
    assert res.status_code == 403


def test_unapproved_dealer_cannot_access_inventory_detail(
    client, dealer_headers, submitted_dealer_profile
):
    res = client.get("/dealer/inventory/1", headers=dealer_headers)
    assert res.status_code == 403
