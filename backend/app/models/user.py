from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    citizen = "citizen"
    collector = "collector"
    dealer = "dealer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    pickup_requests = relationship(
        "PickupRequest", back_populates="citizen", cascade="all, delete-orphan"
    )
    collector_assignments = relationship("CollectorAssignment", back_populates="collector")
    collector_location = relationship(
        "CollectorLocation", back_populates="collector", uselist=False, cascade="all, delete-orphan"
    )
    collector_location_history = relationship(
        "CollectorLocationHistory",
        back_populates="collector",
        cascade="all, delete-orphan",
    )
    pickup_request_events = relationship("PickupRequestEvent", back_populates="actor")
    dealer_profile = relationship(
        "DealerProfile", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    notifications = relationship("Notification", back_populates="user")

    def is_locked(self) -> bool:
        """True while the account is inside a lockout window.

        Tolerates naive datetimes (SQLite stores timezone-less values) and
        timezone-aware values (PostgreSQL) for ``locked_until``.
        """
        if self.locked_until is None:
            return False
        locked_until = self.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        return locked_until > datetime.now(timezone.utc)

    @property
    def email_verified(self) -> bool:
        """True once the account's email has been verified (WIQ-V1-014)."""
        return self.email_verified_at is not None
