from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NotificationType(str, enum.Enum):
    pickup_created = "pickup_created"
    pickup_accepted = "pickup_accepted"
    pickup_started = "pickup_started"
    pickup_collected = "pickup_collected"
    pickup_completed = "pickup_completed"
    weight_recorded = "weight_recorded"
    weight_confirmed = "weight_confirmed"
    weight_disputed = "weight_disputed"
    dispute_resolved = "dispute_resolved"
    dealer_profile_submitted = "dealer_profile_submitted"
    dealer_profile_approved = "dealer_profile_approved"
    dealer_profile_rejected = "dealer_profile_rejected"
    inventory_created = "inventory_created"
    inventory_reserved = "inventory_reserved"
    reservation_cancelled = "reservation_cancelled"
    reservation_expired = "reservation_expired"
    inventory_purchased = "inventory_purchased"
    admin_announcement = "admin_announcement"
    system = "system"


class NotificationStatus(str, enum.Enum):
    unread = "unread"
    read = "read"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_user_type", "user_id", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False), nullable=False, index=True
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False),
        nullable=False,
        default=NotificationStatus.unread,
        server_default=NotificationStatus.unread.value,
        index=True,
    )
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user = relationship("User", back_populates="notifications")
