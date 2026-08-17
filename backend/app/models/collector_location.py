from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CollectorLocation(Base):
    """Latest reported location for a collector.

    One row per collector (unique on ``collector_id``); every update
    replaces the row so reads stay O(1). Updates are also appended to
    :class:`CollectorLocationHistory` for tracking.
    """

    __tablename__ = "collector_locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    collector_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    collector = relationship("User", back_populates="collector_location")


class CollectorLocationHistory(Base):
    """Append-only history of collector location updates."""

    __tablename__ = "collector_location_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    collector_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    collector = relationship("User", back_populates="collector_location_history")
