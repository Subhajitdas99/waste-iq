from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.inventory_lot import InventoryLotStatus


class InventoryLotEventType(str, enum.Enum):
    created = "created"
    updated = "updated"
    status_changed = "status_changed"
    archived = "archived"
    restored = "restored"
    reserved = "reserved"
    reservation_expired = "reservation_expired"


class InventoryLotEvent(Base):
    __tablename__ = "inventory_lot_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inventory_lot_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_lots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[InventoryLotEventType] = mapped_column(
        Enum(InventoryLotEventType, native_enum=False),
        nullable=False,
        index=True,
    )
    previous_status: Mapped[InventoryLotStatus | None] = mapped_column(
        Enum(InventoryLotStatus, native_enum=False),
        nullable=True,
    )
    new_status: Mapped[InventoryLotStatus | None] = mapped_column(
        Enum(InventoryLotStatus, native_enum=False),
        nullable=True,
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    inventory_lot = relationship("InventoryLot", back_populates="events")
    actor = relationship("User")
