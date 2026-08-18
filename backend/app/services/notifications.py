from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select

from app.models.dealer_profile import DealerProfile
from app.models.inventory_lot import InventoryLot
from app.models.marketplace_order import MarketplaceOrder
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.pickup_request import PickupRequest
from app.models.user import User, UserRole
from app.repositories.notifications import NotificationRepository
from app.schemas.notification import (
    NotificationBroadcastRead,
    NotificationBroadcastRequest,
    NotificationBulkActionRead,
    NotificationPageRead,
    NotificationRead,
    NotificationUnreadCountRead,
)
from app.services import notification_formatters as fmt

_MAX_PAGE_SIZE = 50


def _to_schema(notification: Notification) -> NotificationRead:
    return NotificationRead.model_validate(notification)


class NotificationService:
    """Per-user notification CRUD plus unread management."""

    def __init__(self, repository: NotificationRepository | None = None) -> None:
        self._repository = repository or NotificationRepository()

    def create(
        self,
        db,
        *,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        link: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> NotificationRead:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata_json,
        )
        self._repository.create(db, notification)
        db.refresh(notification)
        return _to_schema(notification)

    def list_user(
        self,
        db,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
        status_value: NotificationStatus | None = None,
    ) -> NotificationPageRead:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="page must be at least 1"
            )
        if page_size < 1 or page_size > _MAX_PAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"page_size must be between 1 and {_MAX_PAGE_SIZE}",
            )

        items, total_items, total_pages = self._repository.list_for_user(
            db,
            user.id,
            page=page,
            page_size=page_size,
            status_value=status_value,
        )
        return NotificationPageRead(
            items=[_to_schema(item) for item in items],
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def list_unread(self, db, user: User, *, limit: int = 50) -> list[NotificationRead]:
        return [_to_schema(item) for item in self._repository.list_unread(db, user.id, limit=limit)]

    def count_unread(self, db, user: User) -> NotificationUnreadCountRead:
        return NotificationUnreadCountRead(unread_count=self._repository.count_unread(db, user.id))

    def get_user(self, db, user: User, notification_id: int) -> NotificationRead:
        notification = self._get_user_or_404(db, user.id, notification_id)
        return _to_schema(notification)

    def mark_read(self, db, user: User, notification_id: int) -> NotificationRead:
        notification = self._get_user_or_404(db, user.id, notification_id)
        if notification.status == NotificationStatus.unread:
            self._repository.mark_read(db, notification)
            db.commit()
            db.refresh(notification)
        return _to_schema(notification)

    def mark_all_read(self, db, user: User) -> NotificationBulkActionRead:
        affected = self._repository.mark_all_read(db, user.id)
        db.commit()
        return NotificationBulkActionRead(affected=affected)

    def delete(self, db, user: User, notification_id: int) -> None:
        notification = self._get_user_or_404(db, user.id, notification_id)
        self._repository.delete(db, notification)
        db.commit()

    def delete_read(self, db, user: User) -> NotificationBulkActionRead:
        affected = self._repository.delete_read(db, user.id)
        db.commit()
        return NotificationBulkActionRead(affected=affected)

    def _get_user_or_404(self, db, user_id: int, notification_id: int) -> Notification:
        notification = self._repository.get_for_user(db, user_id, notification_id)
        if notification is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )
        return notification


class NotificationDispatcher:
    """Event-triggered notification send helpers used by the domain services.

    Each helper creates notifications inside the caller's active transaction so
    they commit (or roll back) atomically with the domain change that produced
    them. Senders never commit here — the domain service owns the commit.
    """

    def __init__(self, service: NotificationService | None = None) -> None:
        self._service = service or NotificationService()

    def _notify(
        self,
        db,
        *,
        user_id: int | None,
        type: NotificationType,
        title: str,
        message: str,
        link: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        if user_id is None:
            return
        self._service.create(
            db,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata_json,
        )

    def notify_admins(
        self,
        db,
        message: str,
        *,
        title: str = "Admin Notification",
        link: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        admins = db.execute(select(User).where(User.role == UserRole.admin)).scalars().all()

        for admin in admins:
            self._notify(
                db,
                user_id=admin.id,
                type=NotificationType.system,
                title=title,
                message=message,
                link=link,
                metadata_json=metadata_json,
            )

    # ─── Pickup lifecycle ────────────────────────────────────────────────────

    def notify_pickup_created(self, db, pickup_request: PickupRequest) -> None:
        title, message, link, metadata = fmt.format_pickup_created(pickup_request)
        self._notify(
            db,
            user_id=pickup_request.user_id,
            type=NotificationType.pickup_created,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_pickup_accepted(
        self, db, pickup_request: PickupRequest, collector: User | None
    ) -> None:
        title, message, link, metadata = fmt.format_pickup_accepted(
            pickup_request, collector.name if collector is not None else None
        )
        self._notify(
            db,
            user_id=pickup_request.user_id,
            type=NotificationType.pickup_accepted,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_pickup_started(
        self, db, pickup_request: PickupRequest, collector: User | None
    ) -> None:
        title, message, link, metadata = fmt.format_pickup_started(
            pickup_request, collector.name if collector is not None else None
        )
        self._notify(
            db,
            user_id=pickup_request.user_id,
            type=NotificationType.pickup_started,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_pickup_collected(
        self, db, pickup_request: PickupRequest, collector: User | None
    ) -> None:
        title, message, link, metadata = fmt.format_pickup_collected(
            pickup_request, collector.name if collector is not None else None
        )
        self._notify(
            db,
            user_id=pickup_request.user_id,
            type=NotificationType.pickup_collected,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_pickup_completed(
        self, db, pickup_request: PickupRequest, weight_kg: float | None
    ) -> None:
        title, message, link, metadata = fmt.format_pickup_completed(pickup_request, weight_kg)
        self._notify(
            db,
            user_id=pickup_request.user_id,
            type=NotificationType.pickup_completed,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    # ─── Dealer approval workflow ────────────────────────────────────────────

    def notify_dealer_profile_submitted(self, db, profile: DealerProfile) -> None:
        title, message, link, metadata = fmt.format_dealer_profile_submitted(
            profile, profile.user.name if profile.user is not None else None
        )
        admins = db.execute(select(User).where(User.role == UserRole.admin)).scalars().all()
        for admin in admins:
            self._notify(
                db,
                user_id=admin.id,
                type=NotificationType.dealer_profile_submitted,
                title=title,
                message=message,
                link=link,
                metadata_json=metadata,
            )

    def notify_dealer_profile_approved(self, db, profile: DealerProfile) -> None:
        title, message, link, metadata = fmt.format_dealer_profile_approved(profile)
        self._notify(
            db,
            user_id=profile.user_id,
            type=NotificationType.dealer_profile_approved,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_dealer_profile_rejected(
        self, db, profile: DealerProfile, reason: str | None
    ) -> None:
        title, message, link, metadata = fmt.format_dealer_profile_rejected(profile, reason)
        self._notify(
            db,
            user_id=profile.user_id,
            type=NotificationType.dealer_profile_rejected,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    # ─── Inventory marketplace ───────────────────────────────────────────────

    def notify_inventory_created(self, db, lot: InventoryLot) -> None:
        title, message, link, metadata = fmt.format_inventory_created(lot)
        self._notify(
            db,
            user_id=lot.citizen_id,
            type=NotificationType.inventory_created,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_inventory_reserved(self, db, lot: InventoryLot, dealer: User) -> None:
        seller_title, seller_message, seller_link, seller_metadata = fmt.format_inventory_reserved(
            lot
        )
        self._notify(
            db,
            user_id=lot.citizen_id,
            type=NotificationType.inventory_reserved,
            title=seller_title,
            message=seller_message,
            link=seller_link,
            metadata_json=seller_metadata,
        )
        dealer_title, dealer_message, dealer_link, dealer_metadata = (
            fmt.format_dealer_reservation_confirmation(lot)
        )
        self._notify(
            db,
            user_id=dealer.id,
            type=NotificationType.inventory_reserved,
            title=dealer_title,
            message=dealer_message,
            link=dealer_link,
            metadata_json=dealer_metadata,
        )

    def notify_inventory_purchased(
        self, db, lot: InventoryLot, order: MarketplaceOrder | None
    ) -> None:
        title, message, link, metadata = fmt.format_inventory_purchased(lot, order)
        self._notify(
            db,
            user_id=lot.citizen_id,
            type=NotificationType.inventory_purchased,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_reservation_cancelled(self, db, lot: InventoryLot) -> None:
        title, message, link, metadata = fmt.format_reservation_cancelled(lot)
        self._notify(
            db,
            user_id=lot.citizen_id,
            type=NotificationType.reservation_cancelled,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_reservation_expired(self, db, lot: InventoryLot, dealer_id: int) -> None:
        title, message, link, metadata = fmt.format_reservation_expired(lot)
        self._notify(
            db,
            user_id=dealer_id,
            type=NotificationType.reservation_expired,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )

    def notify_system(
        self,
        db,
        *,
        user_id: int,
        title: str,
        message: str,
        link: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        self._notify(
            db,
            user_id=user_id,
            type=NotificationType.system,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata_json,
        )


class NotificationBroadcaster:
    """Broadcasts an admin announcement to all users (or a filtered role set)."""

    _VALID_ROLES = {role.value for role in UserRole}

    def __init__(self, service: NotificationService | None = None) -> None:
        self._service = service or NotificationService()

    def broadcast(
        self, db, payload: NotificationBroadcastRequest, broadcast_type: NotificationType
    ) -> NotificationBroadcastRead:
        recipient_roles = payload.recipient_roles or []
        for role in recipient_roles:
            if role not in self._VALID_ROLES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid recipient role: {role}",
                )

        statement = select(User.id)
        if recipient_roles:
            statement = statement.where(User.role.in_([UserRole(role) for role in recipient_roles]))
        user_ids = list(db.execute(statement).scalars().all())

        for user_id in user_ids:
            self._service.create(
                db,
                user_id=user_id,
                type=broadcast_type,
                title=payload.title,
                message=payload.message,
                link=payload.link,
            )
        db.commit()

        return NotificationBroadcastRead(
            type=broadcast_type.value,
            title=payload.title,
            message=payload.message,
            link=payload.link,
            recipients_count=len(user_ids),
        )
