from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
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
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pickup_requests = relationship("PickupRequest", back_populates="citizen", cascade="all, delete-orphan")
    collector_assignments = relationship("CollectorAssignment", back_populates="collector")
    pickup_request_events = relationship("PickupRequestEvent", back_populates="actor")
    dealer_profile = relationship("DealerProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
