from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PickupStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    on_the_way = "on_the_way"
    collected = "collected"
    completed = "completed"
    cancelled = "cancelled"


class PickupRequest(Base):
    __tablename__ = "pickup_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    waste_type: Mapped[str] = mapped_column(String(100), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[PickupStatus] = mapped_column(
        Enum(PickupStatus, native_enum=False),
        nullable=False,
        default=PickupStatus.pending,
        server_default=PickupStatus.pending.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    citizen = relationship("User", back_populates="pickup_requests")
    assignment = relationship(
        "CollectorAssignment",
        back_populates="pickup_request",
        cascade="all, delete-orphan",
        uselist=False,
    )
    events = relationship(
        "PickupRequestEvent",
        back_populates="pickup_request",
        cascade="all, delete-orphan",
        order_by="PickupRequestEvent.created_at",
    )
    inventory_lot = relationship(
        "InventoryLot",
        back_populates="pickup_request",
        cascade="all, delete-orphan",
        uselist=False,
    )
