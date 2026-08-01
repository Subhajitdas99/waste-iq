import math
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.dealer_inventory import DealerInventory, DealerInventoryStatus


def get_dealer_inventory(db: Session, dealer_id: int, inventory_id: int) -> DealerInventory | None:
    stmt = select(DealerInventory).where(
        DealerInventory.dealer_id == dealer_id,
        DealerInventory.id == inventory_id,
    )
    return db.scalars(stmt).first()


def get_dealer_inventory_by_pickup(
    db: Session, dealer_id: int, pickup_request_id: int
) -> DealerInventory | None:
    stmt = select(DealerInventory).where(
        DealerInventory.dealer_id == dealer_id,
        DealerInventory.pickup_request_id == pickup_request_id,
    )
    return db.scalars(stmt).first()


def list_dealer_inventories(
    db: Session,
    dealer_id: int,
    page: int = 1,
    page_size: int = 20,
    status: DealerInventoryStatus | None = None,
) -> tuple[Sequence[DealerInventory], int, int]:
    stmt = select(DealerInventory).where(DealerInventory.dealer_id == dealer_id)

    if status:
        stmt = stmt.where(DealerInventory.status == status)

    # count total items
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_items = db.scalar(count_stmt) or 0

    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    stmt = (
        stmt.order_by(DealerInventory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.scalars(stmt).all()

    return items, total_items, total_pages


def create_dealer_inventory(db: Session, obj_in: DealerInventory) -> DealerInventory:
    db.add(obj_in)
    db.commit()
    db.refresh(obj_in)
    return obj_in


def update_dealer_inventory(db: Session, db_obj: DealerInventory) -> DealerInventory:
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_dealer_inventory(db: Session, db_obj: DealerInventory) -> None:
    db.delete(db_obj)
    db.commit()
