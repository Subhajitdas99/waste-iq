from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CollectorAssignment(Base):
    __tablename__ = "collector_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("pickup_requests.id", ondelete="CASCADE"), unique=True
    )
    collector_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    pickup_request = relationship("PickupRequest", back_populates="assignment")
    collector = relationship("User", back_populates="collector_assignments")
