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
from app.models.notification import NotificationType
from app.repositories.notifications import NotificationRepository
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
            dealer_id = lot.reserved_by_dealer_id

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

            # Notify dealer
            if dealer_id is not None:
                try:
                    NotificationDispatcher().notify_reservation_expired(
                        db,
                        lot,
                        dealer_id,
                    )
                except Exception:
                    logger.exception(
                        "Failed to notify dealer %s about expired reservation", dealer_id
                    )

            # persist changes for this lot
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
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.aging_pickup_threshold_days)

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

        dispatcher = NotificationDispatcher()
        notification_repository = NotificationRepository()

        for pickup in pickups:
            metadata = {
                "event": "aging_pickup_alert",
                "pickup_id": str(pickup.id),
            }

            # Prevent duplicate notification for the same pickup.
            if notification_repository.exists_by_metadata(
                db,
                notification_type=NotificationType.system,
                metadata_key="pickup_id",
                metadata_value=str(pickup.id),
            ):
                logger.info(
                    "Aging pickup notification already exists for pickup %s",
                    pickup.id,
                )
                continue

            dispatcher.notify_admins(
                db,
                f"Pickup {pickup.id} has been pending for more than "
                f"{settings.aging_pickup_threshold_days} days.",
                title="Aging Pickup Alert",
                metadata_json=metadata,
            )

        db.commit()

        last_runs["aging_pickups"] = datetime.now(timezone.utc)

    except Exception:
        db.rollback()
        logger.exception("Aging pickup check failed")
        raise

    finally:
        db.close()


# --------------------------------------------------
# Scheduler
# --------------------------------------------------
def start_scheduler() -> None:
    # Disable scheduler during tests
    if settings.environment == "test" or not settings.enable_background_jobs:
        logger.info("Background jobs disabled")
        return

    if scheduler.running:
        return

    if scheduler.get_job("reservation_sweep") is None:
        scheduler.add_job(
            reservation_sweep_job,
            trigger="interval",
            minutes=settings.reservation_sweep_interval_minutes,
            id="reservation_sweep",
            replace_existing=True,
        )

    if scheduler.get_job("aging_pickups") is None:
        scheduler.add_job(
            aging_pickup_alert_job,
            trigger="interval",
            minutes=settings.aging_pickup_interval_minutes,
            id="aging_pickups",
            replace_existing=True,
        )

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
