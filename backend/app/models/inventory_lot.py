from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InventoryLotStatus(str, enum.Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"


class InventoryLot(Base):
    __tablename__ = "inventory_lots"
    __table_args__ = (
        CheckConstraint("weight_kg > 0", name="ck_inventory_lots_weight_positive"),
        CheckConstraint("unit_price_per_kg_snapshot >= 0", name="ck_inventory_lots_unit_price_non_negative"),
        CheckConstraint("total_listed_amount >= 0", name="ck_inventory_lots_total_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pickup_request_id: Mapped[int] = mapped_column(
        ForeignKey("pickup_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    collector_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    material_category_id: Mapped[int] = mapped_column(
        ForeignKey("material_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    material_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price_per_kg_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_listed_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pricing_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("pricing_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_address_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InventoryLotStatus] = mapped_column(
        Enum(InventoryLotStatus, native_enum=False),
        nullable=False,
        default=InventoryLotStatus.available,
        server_default=InventoryLotStatus.available.value,
        index=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pickup_request = relationship("PickupRequest", back_populates="inventory_lot")
    citizen = relationship("User", foreign_keys=[citizen_id])
    collector = relationship("User", foreign_keys=[collector_id])
    material_category = relationship("MaterialCategory", back_populates="inventory_lots")
    pricing_rule = relationship("PricingRule", back_populates="inventory_lots")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    events = relationship(
        "InventoryLotEvent",
        back_populates="inventory_lot",
        cascade="all, delete-orphan",
        order_by="InventoryLotEvent.created_at",
    )
