"""Pure functions that build user-facing notification content from domain objects.

Each formatter returns ``(title, message, link, metadata)`` so senders stay free
of copy and deep-link concerns. Links are frontend routes that the Notification
Center deep-links to via ``<RouterLink>``.
"""

from typing import Any

from app.models.dealer_profile import DealerProfile
from app.models.inventory_lot import InventoryLot
from app.models.marketplace_order import MarketplaceOrder
from app.models.pickup_request import PickupRequest

NotificationContent = tuple[str, str, str | None, dict[str, Any]]


def _pickup_link(pickup_request: PickupRequest) -> str:
    return f"/dashboard/pickups/{pickup_request.id}"


def _lot_link_for_citizen(lot: InventoryLot) -> str | None:
    if lot.pickup_request_id is None:
        return None
    return f"/dashboard/pickups/{lot.pickup_request_id}"


def _lot_link_for_dealer(lot: InventoryLot) -> str:
    return f"/dealer/marketplace/{lot.id}"


def format_pickup_created(pickup_request: PickupRequest) -> NotificationContent:
    return (
        "Pickup request submitted",
        f"Request #{pickup_request.id} ({pickup_request.waste_type}) is queued for a collector.",
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "status": pickup_request.status.value},
    )


def format_pickup_accepted(
    pickup_request: PickupRequest, collector_name: str | None
) -> NotificationContent:
    return (
        "Pickup accepted",
        (
            f"A collector accepted request #{pickup_request.id}."
            if not collector_name
            else f"{collector_name} accepted your request #{pickup_request.id}."
        ),
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "collector_name": collector_name},
    )


def format_pickup_started(
    pickup_request: PickupRequest, collector_name: str | None
) -> NotificationContent:
    return (
        "Collector on the way",
        (
            f"The collector is on the way to request #{pickup_request.id}."
            if not collector_name
            else f"{collector_name} is on the way to request #{pickup_request.id}."
        ),
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "collector_name": collector_name},
    )


def format_pickup_collected(
    pickup_request: PickupRequest, collector_name: str | None
) -> NotificationContent:
    return (
        "Waste collected",
        (
            f"Waste for request #{pickup_request.id} has been collected "
            "and is awaiting final confirmation."
        ),
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "collector_name": collector_name},
    )


def format_weight_verification_pending(
    pickup_request: PickupRequest, weight_kg: float
) -> NotificationContent:
    return (
        "Weight recorded — review your pickup",
        (
            f"Your pickup #{pickup_request.id} has been recorded at {weight_kg:.2f} kg. "
            "Please confirm or dispute the weight."
        ),
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "weight_kg": weight_kg},
    )


def format_weight_confirmed(pickup_request: PickupRequest, weight_kg: float) -> NotificationContent:
    return (
        "Weight confirmed",
        f"You confirmed the weight for pickup #{pickup_request.id}: {weight_kg:.2f} kg.",
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "weight_kg": weight_kg},
    )


def format_weight_disputed(pickup_request: PickupRequest) -> NotificationContent:
    return (
        "Weight disputed — review required",
        f"Citizen disputed the weight for pickup #{pickup_request.id}. Please review.",
        None,
        {"pickup_request_id": pickup_request.id},
    )


def format_dispute_resolved(
    pickup_request: PickupRequest, resolution: str, weight_kg: float | None
) -> NotificationContent:
    weight_note = f" {weight_kg:.2f} kg" if weight_kg is not None else ""
    message = (
        f"Your dispute for pickup #{pickup_request.id} has been resolved: "
        f"{resolution}.{weight_note}"
    )
    return (
        "Dispute resolved",
        message,
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "resolution": resolution, "weight_kg": weight_kg},
    )


def format_pickup_completed(
    pickup_request: PickupRequest, weight_kg: float | None
) -> NotificationContent:
    return (
        "Pickup completed",
        (
            f"Request #{pickup_request.id} completed with {weight_kg:.2f} kg reported."
            if weight_kg is not None
            else f"Request #{pickup_request.id} was completed."
        ),
        _pickup_link(pickup_request),
        {"pickup_request_id": pickup_request.id, "weight_kg": weight_kg},
    )


def format_dealer_profile_submitted(
    profile: DealerProfile, dealer_name: str | None
) -> NotificationContent:
    return (
        "New dealer profile submitted",
        f"{dealer_name or 'A dealer'} submitted their profile for review.",
        None,
        {"dealer_user_id": profile.user_id, "business_name": profile.business_name},
    )


def format_dealer_profile_approved(
    profile: DealerProfile,
) -> NotificationContent:
    return (
        "Dealer profile approved",
        (
            f"Your dealer profile for {profile.business_name} was approved. "
            "You can now access the marketplace."
        ),
        "/dealer/profile",
        {"dealer_user_id": profile.user_id},
    )


def format_dealer_profile_rejected(
    profile: DealerProfile, reason: str | None
) -> NotificationContent:
    message = (
        f"Your dealer profile was rejected. Reason: {reason}."
        if reason
        else "Your dealer profile was rejected. Please review and resubmit."
    )
    return (
        "Dealer profile rejected",
        message,
        "/dealer/profile",
        {"dealer_user_id": profile.user_id, "reason": reason},
    )


def format_inventory_created(lot: InventoryLot) -> NotificationContent:
    return (
        "Inventory listed",
        f"Your waste is now listed as inventory lot {lot.lot_number}.",
        _lot_link_for_citizen(lot),
        {"lot_id": lot.id, "lot_number": lot.lot_number},
    )


def format_inventory_reserved(lot: InventoryLot) -> NotificationContent:
    return (
        "Lot reserved",
        f"Inventory lot {lot.lot_number} has been reserved by a dealer.",
        _lot_link_for_citizen(lot),
        {"lot_id": lot.id, "lot_number": lot.lot_number},
    )


def format_inventory_purchased(
    lot: InventoryLot, order: MarketplaceOrder | None
) -> NotificationContent:
    return (
        "Inventory sold",
        f"Inventory lot {lot.lot_number} was sold for {lot.total_listed_amount:.2f}.",
        _lot_link_for_citizen(lot),
        {
            "lot_id": lot.id,
            "lot_number": lot.lot_number,
            "order_id": order.id if order is not None else None,
        },
    )


def format_reservation_cancelled(lot: InventoryLot) -> NotificationContent:
    return (
        "Reservation cancelled",
        f"The reservation on inventory lot {lot.lot_number} was cancelled.",
        _lot_link_for_citizen(lot),
        {"lot_id": lot.id, "lot_number": lot.lot_number},
    )


def format_reservation_expired(lot: InventoryLot) -> NotificationContent:
    return (
        "Reservation expired",
        f"Your reservation on inventory lot {lot.lot_number} has expired.",
        _lot_link_for_dealer(lot),
        {"lot_id": lot.id, "lot_number": lot.lot_number},
    )


def format_dealer_reservation_confirmation(
    lot: InventoryLot,
) -> NotificationContent:
    return (
        "Inventory reserved",
        f"You reserved inventory lot {lot.lot_number} for 24 hours.",
        _lot_link_for_dealer(lot),
        {"lot_id": lot.id, "lot_number": lot.lot_number},
    )
