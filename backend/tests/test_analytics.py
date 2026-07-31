from datetime import datetime, timedelta, timezone

from app.models.collector_assignment import CollectorAssignment
from app.models.inventory_lot import InventoryLot, InventoryLotStatus, InventoryLotVisibility
from app.models.pickup_request import PickupRequest, PickupStatus

API_PREFIX = "/admin/analytics"


def _naive_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _month_keys(now: datetime, count: int) -> list[str]:
    anchor = now.year * 12 + (now.month - 1)
    return [
        f"{(anchor - offset) // 12:04d}-{(anchor - offset) % 12 + 1:02d}"
        for offset in range(count - 1, -1, -1)
    ]


def _mid_month_ago(now: datetime, months_ago: int) -> datetime:
    month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=15)
    for _ in range(months_ago - 1):
        month_start = (month_start.replace(day=1) - timedelta(days=1)).replace(day=15)
    return month_start


def _create_pickup(
    db_session,
    citizen,
    *,
    status=PickupStatus.pending,
    category=None,
    waste_type="Mixed waste",
    created_at=None,
):
    pickup = PickupRequest(
        user_id=citizen.id,
        waste_type=waste_type,
        category=category,
        address="12 Lake Road, Kolkata, 700029",
        latitude=22.5726,
        longitude=88.3639,
        status=status,
        created_at=created_at or _naive_utc_now(),
    )
    db_session.add(pickup)
    db_session.flush()
    return pickup


def _create_completed_pickup_with_assignment(
    db_session,
    citizen,
    collector,
    *,
    category=None,
    waste_type="Mixed waste",
    weight_kg=10.0,
    created_at=None,
    response_hours=1.0,
):
    created = created_at or _naive_utc_now()
    pickup = _create_pickup(
        db_session,
        citizen,
        status=PickupStatus.completed,
        category=category,
        waste_type=waste_type,
        created_at=created,
    )
    assignment = CollectorAssignment(
        request_id=pickup.id,
        collector_id=collector.id,
        accepted_at=created + timedelta(hours=response_hours),
        completed_at=created + timedelta(hours=response_hours + 1),
        weight_kg=weight_kg,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(pickup)
    return pickup


def _create_sold_lot(
    db_session,
    *,
    pickup,
    dealer_user,
    admin_user,
    material_category,
    weight_kg,
    lot_number,
):
    lot = InventoryLot(
        lot_number=lot_number,
        pickup_request_id=pickup.id,
        citizen_id=pickup.user_id,
        collector_id=pickup.assignment.collector_id,
        material_category_id=material_category.id,
        material_description=pickup.waste_type,
        weight_kg=weight_kg,
        unit_price_per_kg_snapshot=10.0,
        total_listed_amount=weight_kg * 10.0,
        source_city="Kolkata",
        status=InventoryLotStatus.sold,
        visibility=InventoryLotVisibility.visible,
        reserved_by_dealer_id=dealer_user.id,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)
    return lot


# ─── Overview ─────────────────────────────────────────────────────────────────


def test_overview_returns_expected_counts_and_rate(
    client, admin_headers, db_session, citizen_user, collector_user, dealer_user
):
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PET_PLASTIC", weight_kg=10.0
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PAPER", weight_kg=5.0
    )
    _create_pickup(db_session, citizen_user, status=PickupStatus.pending)
    _create_pickup(db_session, citizen_user, status=PickupStatus.cancelled)

    response = client.get(f"{API_PREFIX}/overview", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["total_users"] == 4
    assert payload["citizens"] == 1
    assert payload["collectors"] == 1
    assert payload["dealers"] == 1
    assert payload["total_pickups"] == 4
    assert payload["completed_pickups"] == 2
    assert payload["pending_pickups"] == 1
    assert payload["cancelled_pickups"] == 1
    assert payload["total_weight_kg"] == 15.0
    assert payload["completed_rate"] == 50.0


def test_overview_completed_rate_is_zero_without_pickups(
    client, admin_headers, db_session, citizen_user
):
    response = client.get(f"{API_PREFIX}/overview", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["completed_rate"] == 0.0


# ─── Materials ────────────────────────────────────────────────────────────────


def test_materials_buckets_categories_and_falls_back_to_waste_type(
    client, admin_headers, db_session, citizen_user, collector_user
):
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PET_PLASTIC", waste_type="Bottles"
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PLASTIC", waste_type="Carrier bags"
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PAPER", waste_type="Newspapers"
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category=None, waste_type="Glass bottles"
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="E_WASTE", waste_type="Old phone"
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="ORGANIC", waste_type="Kitchen waste"
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category=None, waste_type="Scrap metal"
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category=None, waste_type="Random items"
    )

    response = client.get(f"{API_PREFIX}/materials", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["plastic"] == 2
    assert payload["paper"] == 1
    assert payload["metal"] == 1
    assert payload["glass"] == 1
    assert payload["e_waste"] == 1
    assert payload["organic"] == 1
    assert payload["other"] == 1


# ─── Monthly ──────────────────────────────────────────────────────────────────


def test_monthly_returns_twelve_zero_filled_months_oldest_first(
    client, admin_headers, db_session, citizen_user, collector_user
):
    now = _naive_utc_now()
    _create_completed_pickup_with_assignment(
        db_session,
        citizen_user,
        collector_user,
        category="PAPER",
        weight_kg=7.5,
        created_at=_mid_month_ago(now, 2),
    )
    _create_pickup(db_session, citizen_user, status=PickupStatus.pending, created_at=now)
    _create_completed_pickup_with_assignment(
        db_session,
        citizen_user,
        collector_user,
        category="PAPER",
        weight_kg=3.0,
        created_at=now - timedelta(days=400),
    )

    response = client.get(f"{API_PREFIX}/monthly", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 12
    assert [entry["month"] for entry in payload] == _month_keys(now, 12)

    by_month = {entry["month"]: entry for entry in payload}
    two_months_ago = _month_keys(now, 12)[-3]
    current_month = _month_keys(now, 12)[-1]
    assert by_month[two_months_ago]["pickup_count"] == 1
    assert by_month[two_months_ago]["completed"] == 1
    assert by_month[two_months_ago]["weight"] == 7.5
    assert by_month[current_month]["pickup_count"] == 1
    assert by_month[current_month]["completed"] == 0
    month_13_ago_key = _mid_month_ago(now, 13).strftime("%Y-%m")
    assert month_13_ago_key not in by_month


# ─── Collector performance ────────────────────────────────────────────────────


def test_collectors_returns_ranked_performance(
    client, admin_headers, db_session, citizen_user, collector_user
):
    _create_completed_pickup_with_assignment(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=10.0,
        response_hours=1.0,
    )
    _create_completed_pickup_with_assignment(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=20.0,
        response_hours=3.0,
    )
    pickup = _create_pickup(db_session, citizen_user, status=PickupStatus.pending)
    assignment = CollectorAssignment(
        request_id=pickup.id,
        collector_id=collector_user.id,
        accepted_at=_naive_utc_now(),
    )
    db_session.add(assignment)
    db_session.commit()

    response = client.get(f"{API_PREFIX}/collectors", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 1
    entry = payload[0]
    assert entry["collector_id"] == collector_user.id
    assert entry["collector_name"] == "Test User"
    assert entry["completed_jobs"] == 2
    assert entry["completion_rate"] == 66.67
    assert entry["average_response_time"] == 2.0


# ─── Dealer performance ───────────────────────────────────────────────────────


def test_dealers_returns_only_dealers_with_sold_material(
    client,
    admin_headers,
    db_session,
    citizen_user,
    collector_user,
    dealer_user,
    admin_user,
    second_dealer_user,
    approved_dealer_profile,
    material_category,
):
    first = _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, weight_kg=10.0
    )
    second = _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, weight_kg=5.0
    )
    _create_sold_lot(
        db_session,
        pickup=first,
        dealer_user=dealer_user,
        admin_user=admin_user,
        material_category=material_category,
        weight_kg=10.0,
        lot_number="WIQ-TEST-000001",
    )
    _create_sold_lot(
        db_session,
        pickup=second,
        dealer_user=dealer_user,
        admin_user=admin_user,
        material_category=material_category,
        weight_kg=5.0,
        lot_number="WIQ-TEST-000002",
    )

    response = client.get(f"{API_PREFIX}/dealers", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 1
    entry = payload[0]
    assert entry["dealer_id"] == dealer_user.id
    assert entry["dealer_name"] == "Test Recyclers Pvt Ltd"
    assert entry["materials_processed"] == 2
    assert entry["total_weight"] == 15.0


# ─── Carbon savings ───────────────────────────────────────────────────────────


def test_carbon_savings_from_completed_weights(
    client, admin_headers, db_session, citizen_user, collector_user
):
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PET_PLASTIC", weight_kg=10.0
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PAPER", weight_kg=5.0
    )

    response = client.get(f"{API_PREFIX}/carbon", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["estimated_co2_saved"] == 6.3
    assert payload["trees_equivalent"] == 0.3
    assert payload["plastic_recycled"] == 10.0
    assert payload["paper_recycled"] == 5.0


def test_carbon_savings_are_zero_without_data(client, admin_headers, db_session, citizen_user):
    response = client.get(f"{API_PREFIX}/carbon", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["estimated_co2_saved"] == 0.0
    assert payload["trees_equivalent"] == 0.0
    assert payload["plastic_recycled"] == 0.0
    assert payload["paper_recycled"] == 0.0


# ─── Rule-based insights ──────────────────────────────────────────────────────


def test_insights_are_generated_from_platform_data(
    client,
    admin_headers,
    db_session,
    citizen_user,
    collector_user,
    dealer_user,
    admin_user,
    material_category,
):
    now = _naive_utc_now()
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PET_PLASTIC", weight_kg=10.0
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PET_PLASTIC", weight_kg=8.0
    )
    _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, category="PAPER", weight_kg=5.0
    )
    _create_completed_pickup_with_assignment(
        db_session,
        citizen_user,
        collector_user,
        category="PAPER",
        weight_kg=4.0,
        created_at=_mid_month_ago(now, 8),
    )
    pickup = _create_completed_pickup_with_assignment(
        db_session, citizen_user, collector_user, weight_kg=3.0
    )
    _create_sold_lot(
        db_session,
        pickup=pickup,
        dealer_user=dealer_user,
        admin_user=admin_user,
        material_category=material_category,
        weight_kg=3.0,
        lot_number="WIQ-TEST-000003",
    )

    response = client.get(f"{API_PREFIX}/insights", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    keys = {insight["key"] for insight in payload}
    assert "most_recycled_material" in keys
    assert "top_collector" in keys
    assert "top_dealer" in keys
    assert "carbon_savings" in keys
    assert "pickup_trend" in keys

    material_insight = next(
        insight for insight in payload if insight["key"] == "most_recycled_material"
    )
    assert material_insight["title"] == "Most Recycled Material"
    assert "Plastic" in material_insight["message"]


def test_insights_are_empty_without_platform_activity(
    client, admin_headers, db_session, citizen_user
):
    response = client.get(f"{API_PREFIX}/insights", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == []
