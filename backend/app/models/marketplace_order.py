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


class MarketplaceOrderStatus(str, enum.Enum):
    completed = "completed"


class MarketplaceOrder(Base):
    __tablename__ = "marketplace_orders"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="ck_marketplace_orders_quantity_positive"),
        CheckConstraint(
            "unit_price_per_kg_snapshot >= 0", name="ck_marketplace_orders_unit_price_non_negative"
        ),
        CheckConstraint(
            "total_amount >= 0", name="ck_marketplace_orders_total_amount_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    inventory_lot_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_lots.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    dealer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price_per_kg_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[MarketplaceOrderStatus] = mapped_column(
        Enum(MarketplaceOrderStatus, native_enum=False),
        nullable=False,
        default=MarketplaceOrderStatus.completed,
        server_default=MarketplaceOrderStatus.completed.value,
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

    inventory_lot = relationship("InventoryLot", foreign_keys=[inventory_lot_id])
    dealer = relationship("User", foreign_keys=[dealer_id])
    transactions = relationship(
        "MarketplaceTransaction",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="MarketplaceTransaction.created_at",
    )
