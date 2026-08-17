from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _make_lot(
    db_session,
    *,
    lot_number: str,
    material_category,
    active_pricing_rule,
    admin_user,
    citizen_user,
    collector_user,
    weight_kg: float = 10.0,
    unit_price: float = 12.5,
    source_city: str = "Kolkata",
    status: str = "available",
    material_description: str = "Mixed recyclables",
):
    from app.models.collector_assignment import CollectorAssignment
    from app.models.inventory_lot import (
        InventoryLot,
        InventoryLotStatus,
        InventoryLotVisibility,
    )
    from app.models.pickup_request import PickupRequest, PickupStatus

    pickup = PickupRequest(
        user_id=citizen_user.id,
        waste_type=material_description,
        address=f"10 Test Road, {source_city}, 700001",
        latitude=22.5,
        longitude=88.3,
        status=PickupStatus.completed,
    )
    db_session.add(pickup)
    db_session.flush()

    assignment = CollectorAssignment(
        request_id=pickup.id,
        collector_id=collector_user.id,
        accepted_at=datetime.now(timezone.utc) - timedelta(hours=2),
        completed_at=datetime.now(timezone.utc),
        weight_kg=weight_kg,
    )
    db_session.add(assignment)
    db_session.flush()

    lot = InventoryLot(
        lot_number=lot_number,
        pickup_request_id=pickup.id,
        citizen_id=citizen_user.id,
        collector_id=collector_user.id,
        material_category_id=material_category.id,
        material_description=material_description,
        weight_kg=weight_kg,
        unit_price_per_kg_snapshot=unit_price,
        total_listed_amount=Decimal(str(round(weight_kg * unit_price, 2))),
        pricing_rule_id=active_pricing_rule.id,
        source_city=source_city,
        source_address_snapshot=pickup.address,
        status=InventoryLotStatus(status),
        visibility=InventoryLotVisibility.visible,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)
    return lot


def _approve_second_dealer(db_session, second_dealer_user):
    from app.models.dealer_profile import DealerApprovalStatus, DealerProfile

    profile = DealerProfile(
        user_id=second_dealer_user.id,
        business_name="Second Recyclers Pvt Ltd",
        owner_name="Second Owner",
        phone="9000000005",
        email="dealer2@test.com",
        address="456 Industrial Area, Kolkata",
        city="Kolkata",
        state="West Bengal",
        postal_code="700004",
        materials_accepted=["Plastic"],
        approval_status=DealerApprovalStatus.approved,
        is_verified=True,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(profile)
    db_session.commit()
    return profile


# ─── Permission gates ────────────────────────────────────────────────────────


def test_unapproved_dealer_cannot_list_marketplace_inventory(
    client: TestClient, dealer_headers: dict, submitted_dealer_profile
):
    response = client.get("/marketplace/inventory", headers=dealer_headers)
    assert response.status_code == 403


def test_dealer_without_profile_cannot_list_marketplace_inventory(
    client: TestClient, dealer_headers: dict
):
    response = client.get("/marketplace/inventory", headers=dealer_headers)
    assert response.status_code == 403


def test_draft_dealer_cannot_list_marketplace_inventory(
    client: TestClient, dealer_headers: dict, draft_dealer_profile
):
    response = client.get("/marketplace/inventory", headers=dealer_headers)
    assert response.status_code == 403


def test_rejected_dealer_cannot_reserve_marketplace_inventory(
    client: TestClient,
    db_session: Session,
    dealer_user,
    dealer_headers: dict,
    inventory_lot,
):
    from app.models.dealer_profile import DealerApprovalStatus, DealerProfile

    profile = db_session.get(DealerProfile, dealer_user.id)
    if profile is None:
        profile = DealerProfile(
            user_id=dealer_user.id,
            business_name="Rejected Recyclers",
            owner_name="Rejected Owner",
            phone="9000000003",
            email="dealer@test.com",
            address="321 Rejected Lane, Kolkata",
            city="Kolkata",
            state="West Bengal",
            postal_code="700005",
            materials_accepted=["Paper"],
        )
        db_session.add(profile)
    profile.approval_status = DealerApprovalStatus.rejected
    db_session.commit()

    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 403


def test_citizen_cannot_access_marketplace(
    client: TestClient, citizen_headers: dict, inventory_lot
):
    response = client.get("/marketplace/inventory", headers=citizen_headers)
    assert response.status_code == 403
    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=citizen_headers
    )
    assert response.status_code == 403


def test_unauthenticated_request_rejected(client: TestClient):
    response = client.get("/marketplace/inventory")
    assert response.status_code == 401


# ─── Inventory listing ───────────────────────────────────────────────────────


def test_list_marketplace_inventory_shows_available_lots(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.get("/marketplace/inventory", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    item = body["items"][0]
    assert item["id"] == inventory_lot.id
    assert item["status"] == "available"
    assert item["material_category_name"] == "PET Plastic"
    assert item["weight_kg"] == 15.5
    assert item["unit_price_per_kg_snapshot"] == 12.5
    assert item["total_listed_amount"] == 193.75
    assert item["currency_code"] == "INR"
    assert item["seller_name"] == "Test User"
    assert item["is_reserved_by_me"] is False


def test_list_marketplace_inventory_hides_sold_lots(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    inventory_lot,
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.sold
    db_session.commit()

    response = client.get("/marketplace/inventory", headers=dealer_headers)
    assert response.status_code == 200
    assert response.json()["total_items"] == 0


def test_list_marketplace_inventory_hides_hidden_lots(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    inventory_lot,
):
    from app.models.inventory_lot import InventoryLotVisibility

    inventory_lot.visibility = InventoryLotVisibility.hidden
    db_session.commit()

    response = client.get("/marketplace/inventory", headers=dealer_headers)
    assert response.status_code == 200
    assert response.json()["total_items"] == 0


def test_list_marketplace_inventory_filter_by_category(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    material_category,
    active_pricing_rule,
    admin_user,
    citizen_user,
    collector_user,
    inventory_lot,
):
    from app.models.material_category import MaterialCategory

    other_category = MaterialCategory(
        code="CARDBOARD",
        name="Cardboard",
        description="Boxes and cartons",
        is_active=True,
        display_order=2,
    )
    db_session.add(other_category)
    db_session.commit()
    db_session.refresh(other_category)

    _make_lot(
        db_session,
        lot_number="LOT-2026-000100",
        material_category=other_category,
        active_pricing_rule=active_pricing_rule,
        admin_user=admin_user,
        citizen_user=citizen_user,
        collector_user=collector_user,
        material_description="Cardboard boxes",
    )

    response = client.get(
        f"/marketplace/inventory?material_category_id={material_category.id}",
        headers=dealer_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["id"] == inventory_lot.id


def test_list_marketplace_inventory_filter_by_city(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    material_category,
    active_pricing_rule,
    admin_user,
    citizen_user,
    collector_user,
    inventory_lot,
):
    _make_lot(
        db_session,
        lot_number="LOT-2026-000101",
        material_category=material_category,
        active_pricing_rule=active_pricing_rule,
        admin_user=admin_user,
        citizen_user=citizen_user,
        collector_user=collector_user,
        source_city="Howrah",
    )

    response = client.get("/marketplace/inventory?city=Howrah", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["source_city"] == "Howrah"


def test_list_marketplace_inventory_search(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    material_category,
    active_pricing_rule,
    admin_user,
    citizen_user,
    collector_user,
    inventory_lot,
):
    _make_lot(
        db_session,
        lot_number="LOT-2026-000102",
        material_category=material_category,
        active_pricing_rule=active_pricing_rule,
        admin_user=admin_user,
        citizen_user=citizen_user,
        collector_user=collector_user,
        material_description="Aluminum cans",
    )

    response = client.get("/marketplace/inventory?search=Aluminum", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["material_description"] == "Aluminum cans"


def test_list_marketplace_inventory_sort_and_pagination(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    material_category,
    active_pricing_rule,
    admin_user,
    citizen_user,
    collector_user,
    inventory_lot,
):
    _make_lot(
        db_session,
        lot_number="LOT-2026-000103",
        material_category=material_category,
        active_pricing_rule=active_pricing_rule,
        admin_user=admin_user,
        citizen_user=citizen_user,
        collector_user=collector_user,
        weight_kg=40.0,
    )

    response = client.get(
        "/marketplace/inventory?sort_by=weight_kg&sort_order=desc&page=1&page_size=1",
        headers=dealer_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["total_items"] == 2
    assert body["total_pages"] == 2
    assert body["items"][0]["weight_kg"] == 40.0


def test_list_marketplace_inventory_invalid_sort_by(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.get("/marketplace/inventory?sort_by=not_a_column", headers=dealer_headers)
    assert response.status_code == 400


def test_list_marketplace_inventory_invalid_page_size(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.get("/marketplace/inventory?page_size=500", headers=dealer_headers)
    assert response.status_code == 400


def test_list_shows_my_reserved_lots(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    reserved = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert reserved.status_code == 200

    response = client.get("/marketplace/inventory", headers=dealer_headers)
    body = response.json()
    assert body["total_items"] == 1
    item = body["items"][0]
    assert item["status"] == "reserved"
    assert item["is_reserved_by_me"] is True


def test_list_hides_lots_reserved_by_other_dealers(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    second_dealer_headers: dict,
    approved_dealer_profile,
    second_dealer_user,
    inventory_lot,
):
    _approve_second_dealer(db_session, second_dealer_user)
    reserved = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=second_dealer_headers
    )
    assert reserved.status_code == 200

    response = client.get("/marketplace/inventory", headers=dealer_headers)
    body = response.json()
    assert body["total_items"] == 0


# ─── Inventory detail ────────────────────────────────────────────────────────


def test_get_marketplace_inventory_detail(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.get(f"/marketplace/inventory/{inventory_lot.id}", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == inventory_lot.id
    assert body["lot_number"] == inventory_lot.lot_number
    assert body["seller_name"] == "Test User"


def test_get_marketplace_inventory_detail_404(
    client: TestClient, dealer_headers: dict, approved_dealer_profile
):
    response = client.get("/marketplace/inventory/999999", headers=dealer_headers)
    assert response.status_code == 404


def test_get_lot_reserved_by_other_dealer_is_hidden(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    second_dealer_headers: dict,
    approved_dealer_profile,
    second_dealer_user,
    inventory_lot,
):
    _approve_second_dealer(db_session, second_dealer_user)
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=second_dealer_headers)

    response = client.get(f"/marketplace/inventory/{inventory_lot.id}", headers=dealer_headers)
    assert response.status_code == 404


# ─── Reservation ─────────────────────────────────────────────────────────────


def test_reserve_marketplace_inventory_success(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "reserved"
    assert body["is_reserved_by_me"] is True
    assert body["reserved_at"] is not None
    assert body["reservation_expires_at"] is not None

    reserved_at = datetime.fromisoformat(body["reserved_at"].replace("Z", "+00:00"))
    expires_at = datetime.fromisoformat(body["reservation_expires_at"].replace("Z", "+00:00"))
    ttl = expires_at - reserved_at
    assert timedelta(hours=23, minutes=55) < ttl < timedelta(hours=24, minutes=5)


def test_duplicate_reservation_conflict(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    first = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert first.status_code == 200

    second = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert second.status_code == 409


def test_reserve_sold_lot_conflict(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    inventory_lot,
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.sold
    db_session.commit()

    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert response.status_code == 409


def test_reserve_creates_reservation_transaction(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)

    response = client.get("/marketplace/transactions", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    transaction = body["items"][0]
    assert transaction["transaction_type"] == "reservation"
    assert transaction["status"] == "completed"
    assert transaction["inventory_lot_id"] == inventory_lot.id
    assert transaction["quantity_kg"] == 15.5
    assert transaction["total_amount"] == 193.75


def test_cancel_reservation_success(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    reserved = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers
    )
    assert reserved.status_code == 200

    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/cancel-reservation",
        headers=dealer_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["reserved_at"] is None
    assert body["reservation_expires_at"] is None

    listing = client.get("/marketplace/inventory", headers=dealer_headers).json()
    assert listing["items"][0]["status"] == "available"


def test_cancel_reservation_when_not_reserved_returns_400(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/cancel-reservation",
        headers=dealer_headers,
    )
    assert response.status_code == 400


def test_cancel_reservation_by_other_dealer_conflict(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    second_dealer_headers: dict,
    approved_dealer_profile,
    second_dealer_user,
    inventory_lot,
):
    _approve_second_dealer(db_session, second_dealer_user)
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=second_dealer_headers)

    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/cancel-reservation",
        headers=dealer_headers,
    )
    assert response.status_code == 409


def test_cancel_creates_cancellation_transaction(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)
    client.post(
        f"/marketplace/inventory/{inventory_lot.id}/cancel-reservation",
        headers=dealer_headers,
    )

    response = client.get("/marketplace/transactions", headers=dealer_headers)
    body = response.json()
    assert body["total_items"] == 2
    types = {item["transaction_type"] for item in body["items"]}
    assert types == {"reservation", "cancellation"}


# ─── Purchase ────────────────────────────────────────────────────────────────


def test_purchase_flow_creates_order_and_transaction(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)

    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    )
    assert response.status_code == 201
    order = response.json()
    assert order["order_number"].startswith("ORD-")
    assert order["inventory_lot_id"] == inventory_lot.id
    assert order["status"] == "completed"
    assert order["quantity_kg"] == 15.5
    assert order["total_amount"] == 193.75
    assert order["dealer_name"] == "Test User"
    transaction_types = {t["transaction_type"] for t in order["transactions"]}
    assert "purchase" in transaction_types

    listing = client.get("/marketplace/inventory", headers=dealer_headers).json()
    assert listing["total_items"] == 0


def test_purchase_without_reservation_rejected(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    )
    assert response.status_code == 400


def test_purchase_reserved_by_another_dealer_rejected(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    second_dealer_headers: dict,
    approved_dealer_profile,
    second_dealer_user,
    inventory_lot,
):
    _approve_second_dealer(db_session, second_dealer_user)
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=second_dealer_headers)

    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    )
    assert response.status_code == 409


def test_double_purchase_rejected(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)
    first = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    )
    assert first.status_code == 201

    second = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    )
    assert second.status_code == 409


def test_purchase_expired_reservation_rejected(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    inventory_lot,
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = approved_dealer_profile.user_id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    response = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    )
    assert response.status_code == 409

    db_session.refresh(inventory_lot)
    assert inventory_lot.status == InventoryLotStatus.reserved


def test_purchase_creates_full_transaction_history(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)
    client.post(f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers)

    response = client.get("/marketplace/transactions", headers=dealer_headers)
    body = response.json()
    assert body["total_items"] == 2
    types = {item["transaction_type"] for item in body["items"]}
    assert types == {"reservation", "purchase"}
    purchase = next(item for item in body["items"] if item["transaction_type"] == "purchase")
    assert purchase["order_id"] is not None


# ─── Orders ──────────────────────────────────────────────────────────────────


def test_list_marketplace_orders(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)
    client.post(f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers)

    response = client.get("/marketplace/orders", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    order = body["items"][0]
    assert order["inventory_lot_id"] == inventory_lot.id
    assert order["status"] == "completed"
    assert order["material_category_name"] == "PET Plastic"


def test_list_orders_pagination(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    material_category,
    active_pricing_rule,
    admin_user,
    citizen_user,
    collector_user,
    inventory_lot,
):
    second_lot = _make_lot(
        db_session,
        lot_number="LOT-2026-000200",
        material_category=material_category,
        active_pricing_rule=active_pricing_rule,
        admin_user=admin_user,
        citizen_user=citizen_user,
        collector_user=collector_user,
        weight_kg=5.0,
    )
    for lot in (inventory_lot, second_lot):
        client.post(f"/marketplace/inventory/{lot.id}/reserve", headers=dealer_headers)
        client.post(f"/marketplace/inventory/{lot.id}/purchase", headers=dealer_headers)

    response = client.get("/marketplace/orders?page=1&page_size=1", headers=dealer_headers)
    body = response.json()
    assert body["total_items"] == 2
    assert body["total_pages"] == 2
    assert len(body["items"]) == 1


def test_get_marketplace_order_detail(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)
    purchased = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    ).json()

    response = client.get(f"/marketplace/orders/{purchased['id']}", headers=dealer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["order_number"] == purchased["order_number"]
    assert len(body["transactions"]) == 2


def test_get_other_dealers_order_returns_404(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    second_dealer_headers: dict,
    approved_dealer_profile,
    second_dealer_user,
    inventory_lot,
):
    _approve_second_dealer(db_session, second_dealer_user)
    client.post(f"/marketplace/inventory/{inventory_lot.id}/reserve", headers=dealer_headers)
    purchased = client.post(
        f"/marketplace/inventory/{inventory_lot.id}/purchase", headers=dealer_headers
    ).json()

    response = client.get(f"/marketplace/orders/{purchased['id']}", headers=second_dealer_headers)
    assert response.status_code == 404


# ─── Transactions ────────────────────────────────────────────────────────────


def test_list_marketplace_transactions_filter_by_type(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    material_category,
    active_pricing_rule,
    admin_user,
    citizen_user,
    collector_user,
    inventory_lot,
):
    second_lot = _make_lot(
        db_session,
        lot_number="LOT-2026-000201",
        material_category=material_category,
        active_pricing_rule=active_pricing_rule,
        admin_user=admin_user,
        citizen_user=citizen_user,
        collector_user=collector_user,
    )
    for lot in (inventory_lot, second_lot):
        client.post(f"/marketplace/inventory/{lot.id}/reserve", headers=dealer_headers)
    client.post(
        f"/marketplace/inventory/{inventory_lot.id}/cancel-reservation",
        headers=dealer_headers,
    )

    response = client.get(
        "/marketplace/transactions?transaction_type=purchase", headers=dealer_headers
    )
    assert response.status_code == 200
    assert response.json()["total_items"] == 0

    response = client.get(
        "/marketplace/transactions?transaction_type=cancellation", headers=dealer_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["transaction_type"] == "cancellation"


def test_transactions_invalid_type_filter_returns_400(
    client: TestClient, dealer_headers: dict, approved_dealer_profile, inventory_lot
):
    response = client.get(
        "/marketplace/transactions?transaction_type=bogus", headers=dealer_headers
    )
    assert response.status_code == 400


def test_expired_reservation_records_expired_transaction(
    client: TestClient,
    db_session: Session,
    dealer_headers: dict,
    approved_dealer_profile,
    inventory_lot,
):
    from app.models.inventory_lot import InventoryLotStatus

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = approved_dealer_profile.user_id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    client.get("/marketplace/inventory", headers=dealer_headers)

    response = client.get("/marketplace/transactions", headers=dealer_headers)
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["transaction_type"] == "reservation_expired"
    assert body["items"][0]["status"] == "expired"
