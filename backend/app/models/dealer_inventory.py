from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DealerInventoryStatus(str, enum.Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"


class DealerInventory(Base):
    __tablename__ = "dealer_inventories"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="ck_dealer_inventories_quantity_positive"),
        CheckConstraint("price_per_kg >= 0", name="ck_dealer_inventories_price_non_negative"),
        CheckConstraint("total_value >= 0", name="ck_dealer_inventories_total_value_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dealer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    pickup_request_id: Mapped[int] = mapped_column(
        ForeignKey("pickup_requests.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    material_type: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quality_grade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[DealerInventoryStatus] = mapped_column(
        Enum(DealerInventoryStatus, native_enum=False),
        nullable=False,
        default=DealerInventoryStatus.available,
        server_default=DealerInventoryStatus.available.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    dealer = relationship("User", foreign_keys=[dealer_id])
    pickup_request = relationship("PickupRequest", foreign_keys=[pickup_request_id])
