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


class MarketplaceTransactionType(str, enum.Enum):
    reservation = "reservation"
    cancellation = "cancellation"
    purchase = "purchase"
    reservation_expired = "reservation_expired"


class MarketplaceTransactionStatus(str, enum.Enum):
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"


class MarketplaceTransaction(Base):
    __tablename__ = "marketplace_transactions"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="ck_marketplace_transactions_quantity_positive"),
        CheckConstraint(
            "unit_price_per_kg_snapshot >= 0",
            name="ck_marketplace_transactions_unit_price_non_negative",
        ),
        CheckConstraint(
            "total_amount >= 0", name="ck_marketplace_transactions_total_amount_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dealer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    inventory_lot_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_lots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("marketplace_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transaction_type: Mapped[MarketplaceTransactionType] = mapped_column(
        Enum(MarketplaceTransactionType, native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[MarketplaceTransactionStatus] = mapped_column(
        Enum(MarketplaceTransactionStatus, native_enum=False),
        nullable=False,
        index=True,
    )
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price_per_kg_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    dealer = relationship("User", foreign_keys=[dealer_id])
    inventory_lot = relationship("InventoryLot", foreign_keys=[inventory_lot_id])
    order = relationship("MarketplaceOrder", back_populates="transactions")
