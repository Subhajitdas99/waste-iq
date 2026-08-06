from datetime import datetime, timedelta, timezone
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.inventory_lot import (
    InventoryLot,
    InventoryLotStatus,
)
from app.models.inventory_lot_event import (
    InventoryLotEvent,
    InventoryLotEventType,
)
from app.models.pickup_request import (
    PickupRequest,
    PickupStatus,
)
from app.services.notifications import NotificationDispatcher

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")

# --------------------------------------------------
# Last Run Tracking
# --------------------------------------------------
last_runs: dict[str, datetime | None] = {
    "reservation_sweep": None,
    "aging_pickups": None,
}


# --------------------------------------------------
# Reservation Sweep Job
# --------------------------------------------------
def reservation_sweep_job() -> None:
    logger.info("Running reservation sweep...")

    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        expired_lots = (
            db.query(InventoryLot)
            .filter(
                InventoryLot.status == InventoryLotStatus.reserved,
                InventoryLot.reservation_expires_at <= now,
            )
            .all()
        )

        logger.info("Found %d expired reservation(s)", len(expired_lots))

        for lot in expired_lots:
            previous_status = lot.status

            # Release reservation
            lot.status = InventoryLotStatus.available
            lot.reserved_by_dealer_id = None
            lot.reserved_at = None
            lot.reservation_expires_at = None

            # Create audit event
            db.add(
                InventoryLotEvent(
                    inventory_lot_id=lot.id,
                    event_type=InventoryLotEventType.reservation_expired,
                    previous_status=previous_status,
                    new_status=InventoryLotStatus.available,
                    actor_user_id=None,
                    event_notes="Reservation expired automatically by scheduler.",
                    metadata_json={},
                )
            )

            # Notify
            NotificationDispatcher.reservation_expired(lot.id)

        db.commit()

        # Update last successful run
        last_runs["reservation_sweep"] = datetime.now(timezone.utc)

    except Exception:
        db.rollback()
        logger.exception("Reservation sweep failed")
        raise

    finally:
        db.close()


# --------------------------------------------------
# Aging Pickup Alert Job
# --------------------------------------------------
def aging_pickup_alert_job() -> None:
    logger.info("Checking aging pickup requests...")

    db = SessionLocal()

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=2)

        pickups = (
            db.query(PickupRequest)
            .filter(
                PickupRequest.status.in_(
                    [
                        PickupStatus.pending,
                        PickupStatus.accepted,
                    ]
                ),
                PickupRequest.created_at <= cutoff,
            )
            .all()
        )

        logger.info("Found %d aging pickup(s)", len(pickups))

        for pickup in pickups:
            NotificationDispatcher.notify_admins(
                f"Pickup {pickup.id} has been pending for more than 2 days."
            )

        # Update last successful run
        last_runs["aging_pickups"] = datetime.now(timezone.utc)

    except Exception:
        logger.exception("Aging pickup check failed")
        raise

    finally:
        db.close()


# --------------------------------------------------
# Scheduler
# --------------------------------------------------
def start_scheduler() -> None:
    # Disable scheduler during tests
    if settings.environment == "test":
        logger.info("Scheduler disabled in test environment")
        return

    if scheduler.running:
        return

    if scheduler.get_job("reservation_sweep") is None:
        scheduler.add_job(
            reservation_sweep_job,
            trigger="interval",
            minutes=1,
            id="reservation_sweep",
            replace_existing=True,
        )

    if scheduler.get_job("aging_pickups") is None:
        scheduler.add_job(
            aging_pickup_alert_job,
            trigger="interval",
            minutes=5,
            id="aging_pickups",
            replace_existing=True,
        )

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")