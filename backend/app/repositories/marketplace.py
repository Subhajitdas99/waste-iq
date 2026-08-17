import math
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.inventory_lot import InventoryLot, InventoryLotStatus, InventoryLotVisibility
from app.models.marketplace_order import MarketplaceOrder, MarketplaceOrderStatus
from app.models.marketplace_transaction import (
    MarketplaceTransaction,
    MarketplaceTransactionStatus,
    MarketplaceTransactionType,
)

SORTABLE_INVENTORY_COLUMNS = {
    "created_at": InventoryLot.created_at,
    "updated_at": InventoryLot.updated_at,
    "weight_kg": InventoryLot.weight_kg,
    "total_listed_amount": InventoryLot.total_listed_amount,
    "unit_price_per_kg_snapshot": InventoryLot.unit_price_per_kg_snapshot,
    "lot_number": InventoryLot.lot_number,
}


def marketplace_lot_query() -> Select[tuple[InventoryLot]]:
    return select(InventoryLot).options(
        selectinload(InventoryLot.material_category),
        selectinload(InventoryLot.citizen),
        selectinload(InventoryLot.pricing_rule),
    )


def get_lot_for_update(db: Session, lot_id: int) -> InventoryLot | None:
    return db.execute(
        select(InventoryLot).where(InventoryLot.id == lot_id).with_for_update()
    ).scalar_one_or_none()


def get_lot_by_id(db: Session, lot_id: int) -> InventoryLot | None:
    return db.execute(marketplace_lot_query().where(InventoryLot.id == lot_id)).scalar_one_or_none()


def list_visible_lots(
    db: Session,
    *,
    dealer_id: int,
    material_category_id: int | None = None,
    city: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[Sequence[InventoryLot], int, int]:
    filters = [
        InventoryLot.archived_at.is_(None),
        InventoryLot.visibility == InventoryLotVisibility.visible,
        or_(
            InventoryLot.status == InventoryLotStatus.available,
            and_(
                InventoryLot.status == InventoryLotStatus.reserved,
                InventoryLot.reserved_by_dealer_id == dealer_id,
            ),
        ),
    ]
    if material_category_id is not None:
        filters.append(InventoryLot.material_category_id == material_category_id)
    if city is not None and city.strip():
        filters.append(InventoryLot.source_city == city.strip())
    if search is not None and search.strip():
        search_term = f"%{search.strip()}%"
        filters.append(
            or_(
                InventoryLot.lot_number.ilike(search_term),
                InventoryLot.material_description.ilike(search_term),
                InventoryLot.source_city.ilike(search_term),
            )
        )

    count_statement = select(func.count()).select_from(
        marketplace_lot_query().where(*filters).subquery()
    )
    total_items = db.scalar(count_statement) or 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    sort_column = SORTABLE_INVENTORY_COLUMNS.get(sort_by, InventoryLot.created_at)
    order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    statement = (
        marketplace_lot_query()
        .where(*filters)
        .order_by(order_clause, InventoryLot.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.execute(statement).unique().scalars().all()

    return items, total_items, total_pages


def find_expired_reserved_lots(db: Session, now: datetime) -> Sequence[InventoryLot]:
    statement = (
        select(InventoryLot)
        .where(
            InventoryLot.status == InventoryLotStatus.reserved,
            InventoryLot.reservation_expires_at.is_not(None),
            InventoryLot.reservation_expires_at < now,
        )
        .options(
            selectinload(InventoryLot.material_category),
            selectinload(InventoryLot.pricing_rule),
        )
    )
    return db.execute(statement).scalars().all()


# ─── Orders ────────────────────────────────────────────────────────────────


def order_query() -> Select[tuple[MarketplaceOrder]]:
    return select(MarketplaceOrder).options(
        selectinload(MarketplaceOrder.inventory_lot).selectinload(InventoryLot.material_category),
        selectinload(MarketplaceOrder.dealer),
    )


def get_order_for_update(db: Session, order_id: int) -> MarketplaceOrder | None:
    return db.execute(
        select(MarketplaceOrder).where(MarketplaceOrder.id == order_id).with_for_update()
    ).scalar_one_or_none()


def get_order_by_id(db: Session, order_id: int) -> MarketplaceOrder | None:
    return db.execute(order_query().where(MarketplaceOrder.id == order_id)).scalar_one_or_none()


def get_order_by_lot_id(db: Session, inventory_lot_id: int) -> MarketplaceOrder | None:
    return db.execute(
        order_query().where(MarketplaceOrder.inventory_lot_id == inventory_lot_id)
    ).scalar_one_or_none()


def list_orders(
    db: Session,
    *,
    dealer_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[MarketplaceOrder], int, int]:
    filters = [MarketplaceOrder.dealer_id == dealer_id]

    count_statement = select(func.count()).select_from(order_query().where(*filters).subquery())
    total_items = db.scalar(count_statement) or 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    statement = (
        order_query()
        .where(*filters)
        .order_by(MarketplaceOrder.created_at.desc(), MarketplaceOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.execute(statement).unique().scalars().all()

    return items, total_items, total_pages


def create_order(
    db: Session,
    *,
    inventory_lot_id: int,
    dealer_id: int,
    quantity_kg: float,
    unit_price_per_kg_snapshot: Decimal,
    total_amount: Decimal,
    currency_code: str,
) -> MarketplaceOrder:
    order = MarketplaceOrder(
        order_number="PENDING",
        inventory_lot_id=inventory_lot_id,
        dealer_id=dealer_id,
        quantity_kg=quantity_kg,
        unit_price_per_kg_snapshot=unit_price_per_kg_snapshot,
        total_amount=total_amount,
        currency_code=currency_code,
        status=MarketplaceOrderStatus.completed,
    )
    db.add(order)
    db.flush()
    order.order_number = f"ORD-{datetime.now().year:04d}-{order.id:06d}"
    return order


# ─── Transactions ──────────────────────────────────────────────────────────


def transaction_query() -> Select[tuple[MarketplaceTransaction]]:
    return select(MarketplaceTransaction).options(
        selectinload(MarketplaceTransaction.inventory_lot).selectinload(
            InventoryLot.material_category
        ),
        selectinload(MarketplaceTransaction.dealer),
    )


def list_transactions(
    db: Session,
    *,
    dealer_id: int,
    transaction_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[MarketplaceTransaction], int, int]:
    filters = [MarketplaceTransaction.dealer_id == dealer_id]
    if transaction_type is not None:
        filters.append(MarketplaceTransaction.transaction_type == transaction_type)

    count_statement = select(func.count()).select_from(
        transaction_query().where(*filters).subquery()
    )
    total_items = db.scalar(count_statement) or 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    statement = (
        transaction_query()
        .where(*filters)
        .order_by(MarketplaceTransaction.created_at.desc(), MarketplaceTransaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.execute(statement).unique().scalars().all()

    return items, total_items, total_pages


def list_transactions_by_lot(
    db: Session, inventory_lot_id: int
) -> Sequence[MarketplaceTransaction]:
    statement = (
        transaction_query()
        .where(MarketplaceTransaction.inventory_lot_id == inventory_lot_id)
        .order_by(MarketplaceTransaction.created_at.asc(), MarketplaceTransaction.id.asc())
    )
    return db.execute(statement).unique().scalars().all()


def create_transaction(
    db: Session,
    *,
    dealer_id: int,
    inventory_lot_id: int,
    order_id: int | None,
    transaction_type: MarketplaceTransactionType,
    status: MarketplaceTransactionStatus,
    quantity_kg: float,
    unit_price_per_kg_snapshot: Decimal,
    total_amount: Decimal,
    currency_code: str,
) -> MarketplaceTransaction:
    transaction = MarketplaceTransaction(
        dealer_id=dealer_id,
        inventory_lot_id=inventory_lot_id,
        order_id=order_id,
        transaction_type=transaction_type,
        status=status,
        quantity_kg=quantity_kg,
        unit_price_per_kg_snapshot=unit_price_per_kg_snapshot,
        total_amount=total_amount,
        currency_code=currency_code,
    )
    db.add(transaction)
    db.flush()
    return transaction
