from datetime import datetime, timedelta, timezone


def test_admin_create_pricing_rule_success(client, admin_headers, material_category):
    response = client.post(
        "/admin/pricing-rules",
        json={
            "material_category_id": material_category.id,
            "city": "Kolkata",
            "unit_price_per_kg": 15.0,
            "currency_code": "INR",
            "is_active": True,
            "effective_from": datetime.now(timezone.utc).isoformat(),
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["unit_price_per_kg"] == 15.0
    assert body["is_active"] is True


def test_create_pricing_rule_for_inactive_category_fails(client, admin_headers, db_session):
    from app.models.material_category import MaterialCategory

    inactive_category = MaterialCategory(
        code="INACTIVE_CAT", name="Inactive Material", is_active=False, display_order=99
    )
    db_session.add(inactive_category)
    db_session.commit()

    response = client.post(
        "/admin/pricing-rules",
        json={
            "material_category_id": inactive_category.id,
            "city": "Kolkata",
            "unit_price_per_kg": 10.0,
            "effective_from": datetime.now(timezone.utc).isoformat(),
        },
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_create_pricing_rule_invalid_date_range_fails(client, admin_headers, material_category):
    now = datetime.now(timezone.utc)
    response = client.post(
        "/admin/pricing-rules",
        json={
            "material_category_id": material_category.id,
            "city": "Kolkata",
            "unit_price_per_kg": 10.0,
            "effective_from": now.isoformat(),
            "effective_to": (now - timedelta(days=1)).isoformat(),
        },
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_create_active_pricing_rule_conflicts_with_existing_active_rule(
    client, admin_headers, material_category, active_pricing_rule
):
    response = client.post(
        "/admin/pricing-rules",
        json={
            "material_category_id": material_category.id,
            "city": "Kolkata",
            "unit_price_per_kg": 20.0,
            "is_active": True,
            "effective_from": datetime.now(timezone.utc).isoformat(),
        },
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_create_inactive_pricing_rule_does_not_conflict(
    client, admin_headers, material_category, active_pricing_rule
):
    """Inactive rules can coexist with an active one for the same category+city."""
    response = client.post(
        "/admin/pricing-rules",
        json={
            "material_category_id": material_category.id,
            "city": "Kolkata",
            "unit_price_per_kg": 20.0,
            "is_active": False,
            "effective_from": datetime.now(timezone.utc).isoformat(),
        },
        headers=admin_headers,
    )
    assert response.status_code == 201


def test_update_pricing_rule_price(client, admin_headers, active_pricing_rule):
    response = client.patch(
        f"/admin/pricing-rules/{active_pricing_rule.id}",
        json={"unit_price_per_kg": 18.75},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["unit_price_per_kg"] == 18.75


def test_deactivate_pricing_rule(client, admin_headers, active_pricing_rule):
    response = client.post(
        f"/admin/pricing-rules/{active_pricing_rule.id}/deactivate", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_reactivate_pricing_rule_success(client, admin_headers, active_pricing_rule):
    client.post(f"/admin/pricing-rules/{active_pricing_rule.id}/deactivate", headers=admin_headers)
    response = client.post(
        f"/admin/pricing-rules/{active_pricing_rule.id}/activate", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_activate_pricing_rule_conflicting_with_another_active_rule_fails(
    client, admin_headers, material_category, active_pricing_rule
):
    deactivated = client.post(
        "/admin/pricing-rules",
        json={
            "material_category_id": material_category.id,
            "city": "Kolkata",
            "unit_price_per_kg": 25.0,
            "is_active": False,
            "effective_from": datetime.now(timezone.utc).isoformat(),
        },
        headers=admin_headers,
    ).json()

    response = client.post(
        f"/admin/pricing-rules/{deactivated['id']}/activate", headers=admin_headers
    )
    assert response.status_code == 400


def test_pricing_rule_future_effective_from_not_yet_active_for_lot_creation(
    client, admin_headers, completed_pickup_with_assignment, material_category, db_session
):
    """
    A rule with effective_from in the future should NOT be
    resolvable as 'active' for lot pricing.
    """
    from app.models.pricing_rule import PricingRule

    future_rule = PricingRule(
        material_category_id=material_category.id,
        city="Kolkata",
        unit_price_per_kg=99.0,
        currency_code="INR",
        is_active=True,
        effective_from=datetime.now(timezone.utc) + timedelta(days=5),
        effective_to=None,
    )
    db_session.add(future_rule)
    db_session.commit()

    response = client.post(
        "/admin/inventory-lots",
        json={
            "pickup_request_id": completed_pickup_with_assignment.id,
            "material_category_id": material_category.id,
        },
        headers=admin_headers,
    )
    # No currently-active rule exists (the only one is in the future), so lot creation must fail.
    assert response.status_code == 400


def test_pricing_rule_expired_effective_to_not_active_for_lot_creation(
    client, admin_headers, completed_pickup_with_assignment, material_category, db_session
):
    from app.models.pricing_rule import PricingRule

    expired_rule = PricingRule(
        material_category_id=material_category.id,
        city="Kolkata",
        unit_price_per_kg=8.0,
        currency_code="INR",
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=10),
        effective_to=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(expired_rule)
    db_session.commit()

    response = client.post(
        "/admin/inventory-lots",
        json={
            "pickup_request_id": completed_pickup_with_assignment.id,
            "material_category_id": material_category.id,
        },
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_collector_cannot_create_pricing_rule(client, collector_headers, material_category):
    response = client.post(
        "/admin/pricing-rules",
        json={
            "material_category_id": material_category.id,
            "city": "Kolkata",
            "unit_price_per_kg": 10.0,
            "effective_from": datetime.now(timezone.utc).isoformat(),
        },
        headers=collector_headers,
    )
    assert response.status_code == 403
