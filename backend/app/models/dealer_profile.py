from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DealerApprovalStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class DealerProfile(Base):
    __tablename__ = "dealer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    business_name: Mapped[str] = mapped_column(String(160), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    gst_number: Mapped[str | None] = mapped_column(String(30), nullable=True, unique=True)
    license_number: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    business_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    materials_accepted: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    approval_status: Mapped[DealerApprovalStatus] = mapped_column(
        Enum(DealerApprovalStatus, native_enum=False),
        nullable=False,
        default=DealerApprovalStatus.draft,
        server_default=DealerApprovalStatus.draft.value,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="dealer_profile")
    events = relationship(
        "DealerProfileEvent",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="DealerProfileEvent.created_at",
    )
