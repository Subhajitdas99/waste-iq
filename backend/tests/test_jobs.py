from datetime import datetime, timedelta, timezone

from app.models.inventory_lot import InventoryLot, InventoryLotStatus
from app.models.inventory_lot_event import (
    InventoryLotEvent,
    InventoryLotEventType,
)
from app.models.notification import Notification, NotificationType
from app.models.pickup_request import PickupRequest, PickupStatus
from app.services import jobs


def test_reservation_sweep_releases_expired_lot(
    db_session,
    inventory_lot,
    dealer_user,
    jobs_session_factory,
    monkeypatch,
):
    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = dealer_user.id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        jobs_session_factory,
    )

    jobs.reservation_sweep_job()

    lot = (
        db_session.query(type(inventory_lot))
        .filter(type(inventory_lot).id == inventory_lot.id)
        .one()
    )

    assert lot.status == InventoryLotStatus.available
    assert lot.reserved_by_dealer_id is None
    assert lot.reserved_at is None
    assert lot.reservation_expires_at is None

    event = (
        db_session.query(InventoryLotEvent)
        .filter(
            InventoryLotEvent.inventory_lot_id == inventory_lot.id,
            InventoryLotEvent.event_type == InventoryLotEventType.reservation_expired,
        )
        .one()
    )

    assert event.new_status == InventoryLotStatus.available


def test_reservation_sweep_ignores_unexpired_lot(
    db_session,
    inventory_lot,
    dealer_user,
    jobs_session_factory,
    monkeypatch,
):
    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = dealer_user.id
    inventory_lot.reserved_at = datetime.now(timezone.utc)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.commit()

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        jobs_session_factory,
    )

    jobs.reservation_sweep_job()

    lot = (
        db_session.query(type(inventory_lot))
        .filter(type(inventory_lot).id == inventory_lot.id)
        .one()
    )

    assert lot.status == InventoryLotStatus.reserved
    assert lot.reserved_by_dealer_id == dealer_user.id


def test_aging_pickup_alert_notifies_admin(
    db_session,
    citizen_user,
    admin_user,
    jobs_session_factory,
    monkeypatch,
):
    pickup = PickupRequest(
        user_id=citizen_user.id,
        waste_type="Plastic bottles",
        address="12 Lake Road, Kolkata, 700029",
        latitude=22.5726,
        longitude=88.3639,
        status=PickupStatus.pending,
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
    )
    db_session.add(pickup)
    db_session.commit()
    db_session.refresh(pickup)

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        jobs_session_factory,
    )

    jobs.aging_pickup_alert_job()
    db_session.expire_all()

    notifications = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == admin_user.id,
            Notification.type == NotificationType.system,
        )
        .all()
    )

    assert len(notifications) == 1
    assert notifications[0].title == "Aging Pickup Alert"
    assert notifications[0].metadata_json["event"] == "aging_pickup_alert"
    assert notifications[0].metadata_json["pickup_id"] == str(pickup.id)


def test_aging_pickup_alert_is_idempotent(
    db_session,
    citizen_user,
    admin_user,
    jobs_session_factory,
    monkeypatch,
):
    pickup = PickupRequest(
        user_id=citizen_user.id,
        waste_type="Plastic bottles",
        address="12 Lake Road, Kolkata, 700029",
        latitude=22.5726,
        longitude=88.3639,
        status=PickupStatus.pending,
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
    )
    db_session.add(pickup)
    db_session.commit()
    db_session.refresh(pickup)

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        jobs_session_factory,
    )

    jobs.aging_pickup_alert_job()
    jobs.aging_pickup_alert_job()

    notifications = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == admin_user.id,
            Notification.type == NotificationType.system,
        )
        .all()
    )

    assert len(notifications) == 1


def test_aging_pickup_alert_handles_accepted_pickup(
    db_session,
    citizen_user,
    admin_user,
    jobs_session_factory,
    monkeypatch,
):
    pickup = PickupRequest(
        user_id=citizen_user.id,
        waste_type="Plastic bottles",
        address="12 Lake Road, Kolkata, 700029",
        latitude=22.5726,
        longitude=88.3639,
        status=PickupStatus.accepted,
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
    )
    db_session.add(pickup)
    db_session.commit()

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        jobs_session_factory,
    )

    jobs.aging_pickup_alert_job()
    db_session.expire_all()

    notification = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == admin_user.id,
            Notification.type == NotificationType.system,
        )
        .one()
    )

    assert notification.title == "Aging Pickup Alert"


def test_reservation_sweep_creates_expired_transaction(
    db_session,
    inventory_lot,
    dealer_user,
    jobs_session_factory,
    monkeypatch,
):
    from app.models.marketplace_transaction import (
        MarketplaceTransaction,
        MarketplaceTransactionStatus,
        MarketplaceTransactionType,
    )

    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = dealer_user.id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        jobs_session_factory,
    )

    jobs.reservation_sweep_job()

    transaction = (
        db_session.query(MarketplaceTransaction)
        .filter(
            MarketplaceTransaction.inventory_lot_id == inventory_lot.id,
            MarketplaceTransaction.transaction_type
            == MarketplaceTransactionType.reservation_expired,
        )
        .one()
    )

    assert transaction.dealer_id == dealer_user.id
    assert transaction.status == MarketplaceTransactionStatus.expired
    assert transaction.order_id is None
    assert transaction.quantity_kg == 15.5
    assert transaction.total_amount == inventory_lot.total_listed_amount


def test_reservation_sweep_does_not_override_concurrent_purchase(
    db_session,
    inventory_lot,
    dealer_user,
    jobs_session_factory,
    monkeypatch,
):
    inventory_lot.status = InventoryLotStatus.reserved
    inventory_lot.reserved_by_dealer_id = dealer_user.id
    inventory_lot.reserved_at = datetime.now(timezone.utc) - timedelta(hours=25)
    inventory_lot.reservation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    sweep_db = jobs_session_factory()
    purchase_db = jobs_session_factory()

    try:
        original_execute = sweep_db.execute

        def interleaved_execute(stmt, *args, **kwargs):
            result = original_execute(stmt, *args, **kwargs)
            if hasattr(stmt, "compile") and "FROM inventory_lots" in str(
                stmt.compile(compile_kwargs={"literal_binds": True})
            ):
                # The sweep has read its stale snapshot; a dealer purchase
                # now commits status=sold before the sweep writes.
                purchase_db.expire_all()
                purchased_lot = (
                    purchase_db.query(InventoryLot)
                    .with_for_update()
                    .filter(InventoryLot.id == inventory_lot.id)
                    .one()
                )
                purchased_lot.status = InventoryLotStatus.sold
                purchase_db.commit()
            return result

        monkeypatch.setattr(sweep_db, "execute", interleaved_execute)
        monkeypatch.setattr(jobs, "SessionLocal", lambda: sweep_db)

        jobs.reservation_sweep_job()

        db_session.refresh(inventory_lot)
        assert inventory_lot.status == InventoryLotStatus.sold

        expired_events = (
            db_session.query(InventoryLotEvent)
            .filter(
                InventoryLotEvent.inventory_lot_id == inventory_lot.id,
                InventoryLotEvent.event_type == InventoryLotEventType.reservation_expired,
            )
            .count()
        )
        assert expired_events == 0

        from app.models.marketplace_transaction import MarketplaceTransaction

        assert db_session.query(MarketplaceTransaction).count() == 0
        assert db_session.query(Notification).count() == 0
    finally:
        sweep_db.close()
        purchase_db.close()


def test_jobs_status_requires_authentication(client):
    response = client.get("/admin/jobs/status")

    assert response.status_code == 401


def test_jobs_status_denied_for_non_admin_roles(
    client,
    citizen_headers,
    dealer_headers,
    collector_headers,
):
    for headers in (citizen_headers, dealer_headers, collector_headers):
        response = client.get("/admin/jobs/status", headers=headers)
        assert response.status_code == 403


def test_jobs_status_allowed_for_admin(client, admin_headers):
    response = client.get("/admin/jobs/status", headers=admin_headers)

    assert response.status_code == 200
