from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.dealer_profile import DealerApprovalStatus


class DealerProfileEvent(Base):
    __tablename__ = "dealer_profile_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("dealer_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[DealerApprovalStatus] = mapped_column(
        Enum(DealerApprovalStatus, native_enum=False),
        nullable=False,
        default=DealerApprovalStatus.draft,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    profile = relationship("DealerProfile", back_populates="events")
    actor = relationship("User", foreign_keys=[actor_user_id])
