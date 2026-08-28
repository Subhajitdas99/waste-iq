from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DisputeResolution(str, enum.Enum):
    upheld = "upheld"
    corrected = "corrected"


class PickupDispute(Base):
    __tablename__ = "pickup_disputes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("pickup_requests.id", ondelete="CASCADE"), unique=True, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    disputed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[DisputeResolution | None] = mapped_column(
        Enum(DisputeResolution, native_enum=False), nullable=True
    )
    resolved_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    pickup_request = relationship("PickupRequest", back_populates="dispute")
    resolved_by = relationship("User")
