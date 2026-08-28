"""Tests for WIQ-V1-052 Pilot Metrics & Operational Dashboard.

Validates the admin-facing `/admin/analytics/pilot` endpoint and the underlying
service aggregations. Reliability signals that cannot be derived from
authoritative state must always be returned as N/A — never as misleading
zeros.
"""

from datetime import datetime, timedelta, timezone

from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_dispute import DisputeResolution, PickupDispute
from app.models.pickup_request import PickupRequest, PickupStatus

API_PREFIX = "/admin/analytics/pilot"


def _naive_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _create_pickup(
    db_session,
    citizen,
    *,
    status=PickupStatus.pending,
    category=None,
    waste_type="Mixed waste",
    estimated_weight_kg=None,
    created_at=None,
):
    pickup = PickupRequest(
        user_id=citizen.id,
        waste_type=waste_type,
        category=category,
        address="12 Lake Road, Kolkata, 700029",
        latitude=22.5726,
        longitude=88.3639,
        estimated_weight_kg=estimated_weight_kg,
        status=status,
        created_at=created_at or _naive_utc_now(),
    )
    db_session.add(pickup)
    db_session.flush()
    return pickup


def _create_completed_pickup(
    db_session,
    citizen,
    collector,
    *,
    category="PET_PLASTIC",
    waste_type="Mixed waste",
    weight_kg=10.0,
    estimated_weight_kg=None,
    created_at=None,
    response_hours=1.0,
    collection_hours=1.0,
):
    created = created_at or _naive_utc_now()
    pickup = _create_pickup(
        db_session,
        citizen,
        status=PickupStatus.completed,
        category=category,
        waste_type=waste_type,
        estimated_weight_kg=estimated_weight_kg,
        created_at=created,
    )
    assignment = CollectorAssignment(
        request_id=pickup.id,
        collector_id=collector.id,
        accepted_at=created + timedelta(hours=response_hours),
        completed_at=created + timedelta(hours=response_hours + collection_hours),
        weight_kg=weight_kg,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(pickup)
    return pickup


def _create_dispute(
    db_session,
    pickup,
    *,
    resolution: DisputeResolution | None = None,
    resolved_weight_kg: float | None = None,
):
    dispute = PickupDispute(
        request_id=pickup.id,
        reason="Weight seems too high",
        resolution=resolution,
        resolved_weight_kg=resolved_weight_kg,
    )
    db_session.add(dispute)
    db_session.commit()
    db_session.refresh(dispute)
    return dispute


# ─── Empty / safe defaults ────────────────────────────────────────────────────


def test_pilot_metrics_empty_state_returns_safe_defaults(client, admin_headers, db_session):
    response = client.get(API_PREFIX, headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    # Window falls back to a 30-day window when there are no requests.
    assert payload["window"]["days"] == 30
    assert payload["window"]["start"] is not None
    assert payload["window"]["end"] is not None

    # Collection KPIs are zeroed safely.
    assert payload["collection"]["total_pickups"] == 0
    assert payload["collection"]["completed_pickups"] == 0
    assert payload["collection"]["cancelled_pickups"] == 0
    assert payload["collection"]["completion_rate"] == 0.0
    assert payload["collection"]["total_weight_kg"] == 0.0
    assert payload["collection"]["average_weight_kg"] == 0.0
    assert payload["collection"]["active_citizens"] == 0
    assert payload["collection"]["active_collectors"] == 0

    # Timing fields are null (not zero) when no data exists.
    timing = payload["timing"]
    assert timing["median_request_to_acceptance_hours"] is None
    assert timing["median_acceptance_to_completion_hours"] is None
    assert timing["median_request_to_completion_hours"] is None
    assert timing["average_request_to_acceptance_hours"] is None
    assert timing["average_acceptance_to_completion_hours"] is None
    assert timing["sample_size"] == 0

    # Weight quality: counts are zero, ratio/delta are null.
    wq = payload["weight_quality"]
    assert wq["pickups_with_estimate"] == 0
    assert wq["pickups_with_recorded_weight"] == 0
    assert wq["estimate_vs_actual_ratio"] is None
    assert wq["median_absolute_estimate_delta_kg"] is None
    assert wq["disputed_pickups"] == 0
    assert wq["disputes_upheld"] == 0
    assert wq["disputes_corrected"] == 0

    # Reliability: all signals must be N/A.
    rel = payload["reliability"]
    assert rel["api_error_rate"] is None
    assert rel["api_error_rate_available"] is False
    assert rel["notification_failure_rate"] is None
    assert rel["notification_failure_rate_available"] is False
    assert rel["background_job_failures"] is None
    assert rel["background_job_failures_available"] is False
    assert rel["platform_uptime_seconds"] is None
    assert rel["platform_uptime_available"] is False
    # Notes are surfaced so admins know why.
    assert rel["api_error_rate_note"]
    assert rel["notification_failure_rate_note"]
    assert rel["background_job_failures_note"]
    assert rel["platform_uptime_note"]


# ─── Collection KPIs ─────────────────────────────────────────────────────────


def test_pilot_collection_kpis_aggregate_platform_state(
    client, admin_headers, db_session, citizen_user, collector_user
):
    _create_completed_pickup(db_session, citizen_user, collector_user, weight_kg=10.0)
    _create_completed_pickup(db_session, citizen_user, collector_user, weight_kg=5.0)
    _create_pickup(db_session, citizen_user, status=PickupStatus.pending)
    _create_pickup(db_session, citizen_user, status=PickupStatus.cancelled)

    response = client.get(API_PREFIX, headers=admin_headers)
    assert response.status_code == 200
    collection = response.json()["collection"]

    assert collection["total_pickups"] == 4
    assert collection["completed_pickups"] == 2
    assert collection["cancelled_pickups"] == 1
    assert collection["completion_rate"] == 50.0
    assert collection["total_weight_kg"] == 15.0
    assert collection["average_weight_kg"] == 7.5
    assert collection["active_citizens"] == 1
    assert collection["active_collectors"] == 1


# ─── Timing ──────────────────────────────────────────────────────────────────


def test_pilot_timing_computes_median_and_average_hours(
    client, admin_headers, db_session, citizen_user, collector_user
):
    _create_completed_pickup(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=10.0,
        response_hours=1.0,
        collection_hours=2.0,
    )
    _create_completed_pickup(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=5.0,
        response_hours=3.0,
        collection_hours=4.0,
    )

    response = client.get(API_PREFIX, headers=admin_headers)
    assert response.status_code == 200
    timing = response.json()["timing"]

    assert timing["sample_size"] == 2
    # median of {1, 3} = 2
    assert timing["median_request_to_acceptance_hours"] == 2.0
    assert timing["average_request_to_acceptance_hours"] == 2.0
    # median of {2, 4} = 3
    assert timing["median_acceptance_to_completion_hours"] == 3.0
    assert timing["average_acceptance_to_completion_hours"] == 3.0
    # request to completion = response + collection
    # hours = {1+2, 3+4} = {3, 7}; median = 5
    assert timing["median_request_to_completion_hours"] == 5.0


# ─── Weight quality ──────────────────────────────────────────────────────────


def test_pilot_weight_quality_estimate_vs_recorded_and_disputes(
    client, admin_headers, db_session, citizen_user, collector_user
):
    pickup_upheld = _create_completed_pickup(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=10.0,
        estimated_weight_kg=8.0,
    )
    _create_dispute(db_session, pickup_upheld, resolution=DisputeResolution.upheld)

    pickup_corrected = _create_completed_pickup(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=6.0,
        estimated_weight_kg=10.0,
    )
    _create_dispute(
        db_session,
        pickup_corrected,
        resolution=DisputeResolution.corrected,
        resolved_weight_kg=6.0,
    )

    pickup_no_estimate = _create_completed_pickup(
        db_session, citizen_user, collector_user, weight_kg=4.0
    )
    assert pickup_no_estimate.estimated_weight_kg is None

    response = client.get(API_PREFIX, headers=admin_headers)
    assert response.status_code == 200
    wq = response.json()["weight_quality"]

    assert wq["pickups_with_estimate"] == 2
    assert wq["pickups_with_recorded_weight"] == 3
    # ratios: 10/8 = 1.25, 6/10 = 0.60; mean = 0.925 -> 0.93 (2dp)
    assert wq["estimate_vs_actual_ratio"] == 0.93
    # deltas: |10-8| = 2, |6-10| = 4; median = 3.0
    assert wq["median_absolute_estimate_delta_kg"] == 3.0
    assert wq["disputed_pickups"] == 2
    assert wq["disputes_upheld"] == 1
    assert wq["disputes_corrected"] == 1


# ─── Activity windows ────────────────────────────────────────────────────────


def test_pilot_activity_window_7_and_30_days(
    client, admin_headers, db_session, citizen_user, collector_user
):
    now = _naive_utc_now()
    # within 7 days: completed
    _create_completed_pickup(db_session, citizen_user, collector_user, weight_kg=5.0)
    # within 30 days (but more than 7 days ago): completed
    _create_completed_pickup(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=3.0,
        created_at=now - timedelta(days=20),
    )
    # within 7 days: pending (not completed)
    _create_pickup(db_session, citizen_user, status=PickupStatus.pending)
    # older than 30 days: should be ignored
    _create_completed_pickup(
        db_session,
        citizen_user,
        collector_user,
        weight_kg=2.0,
        created_at=now - timedelta(days=60),
    )

    response = client.get(API_PREFIX, headers=admin_headers)
    assert response.status_code == 200
    activity = response.json()["activity"]

    assert activity["pickups_last_7_days"] == 2
    assert activity["pickups_last_30_days"] == 3
    assert activity["completed_last_7_days"] == 1
    assert activity["completed_last_30_days"] == 2


# ─── RBAC ────────────────────────────────────────────────────────────────────


def test_pilot_metrics_requires_admin(client, citizen_headers, collector_headers, dealer_headers):
    for headers in (citizen_headers, collector_headers, dealer_headers):
        response = client.get(API_PREFIX, headers=headers)
        assert (
            response.status_code == 403
        ), f"Expected 403 for non-admin, got {response.status_code}"


# ─── Reliability invariant ───────────────────────────────────────────────────


def test_pilot_reliability_signals_are_never_fabricated(
    client, admin_headers, db_session, citizen_user, collector_user
):
    # Even with real platform activity, reliability signals must remain N/A
    # because the underlying data is not captured.
    _create_completed_pickup(db_session, citizen_user, collector_user, weight_kg=10.0)

    response = client.get(API_PREFIX, headers=admin_headers)
    assert response.status_code == 200
    rel = response.json()["reliability"]

    assert rel["api_error_rate"] is None
    assert rel["api_error_rate_available"] is False
    assert rel["notification_failure_rate"] is None
    assert rel["notification_failure_rate_available"] is False
    assert rel["background_job_failures"] is None
    assert rel["background_job_failures_available"] is False
    assert rel["platform_uptime_seconds"] is None
    assert rel["platform_uptime_available"] is False
    assert isinstance(rel["background_job_last_runs"], dict)
