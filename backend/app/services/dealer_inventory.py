from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dealer_inventory import DealerInventory, DealerInventoryStatus
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User
from app.repositories import dealer_inventory as repo
from app.schemas.dealer_inventory import (
    DealerInventoryCreate,
    DealerInventoryPageRead,
    DealerInventoryRead,
    DealerInventoryUpdate,
)
from app.services.dealer_approval import ensure_approved_dealer


def _ensure_approved_dealer(db: Session, current_user: User) -> None:
    ensure_approved_dealer(db, current_user)


def _to_schema(inventory: DealerInventory) -> DealerInventoryRead:
    return DealerInventoryRead.model_validate(inventory)


def list_dealer_inventories(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
) -> DealerInventoryPageRead:
    _ensure_approved_dealer(db, current_user)
    parsed_status = None
    if status_filter:
        try:
            parsed_status = DealerInventoryStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter"
            )

    items, total_items, total_pages = repo.list_dealer_inventories(
        db, current_user.id, page, page_size, parsed_status
    )

    return DealerInventoryPageRead(
        items=[_to_schema(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


def get_dealer_inventory(db: Session, current_user: User, inventory_id: int) -> DealerInventoryRead:
    return _to_schema(_get_dealer_inventory_model(db, current_user, inventory_id))


def _get_dealer_inventory_model(
    db: Session, current_user: User, inventory_id: int
) -> DealerInventory:
    _ensure_approved_dealer(db, current_user)
    inv = repo.get_dealer_inventory(db, current_user.id, inventory_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dealer inventory not found"
        )
    return inv


def create_dealer_inventory(
    db: Session, current_user: User, payload: DealerInventoryCreate
) -> DealerInventoryRead:
    _ensure_approved_dealer(db, current_user)
    # 1. Validate pickup request exists and is completed
    pickup = db.scalars(
        select(PickupRequest).where(PickupRequest.id == payload.pickup_request_id)
    ).first()
    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )
    if pickup.status != PickupStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory can only be created from completed pickups",
        )

    # 2. Check if inventory already exists for this pickup for this dealer
    existing = repo.get_dealer_inventory_by_pickup(db, current_user.id, payload.pickup_request_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already created for this pickup",
        )

    # 3. Compute total value
    total_value = Decimal(str(payload.quantity_kg)) * payload.price_per_kg

    inv = DealerInventory(
        dealer_id=current_user.id,
        pickup_request_id=payload.pickup_request_id,
        material_type=payload.material_type,
        category=payload.category,
        quantity_kg=payload.quantity_kg,
        price_per_kg=payload.price_per_kg,
        total_value=total_value,
        quality_grade=payload.quality_grade,
        status=DealerInventoryStatus.available,
    )
    return _to_schema(repo.create_dealer_inventory(db, inv))


def update_dealer_inventory(
    db: Session, current_user: User, inventory_id: int, payload: DealerInventoryUpdate
) -> DealerInventoryRead:
    inv = _get_dealer_inventory_model(db, current_user, inventory_id)

    if payload.material_type is not None:
        inv.material_type = payload.material_type
    if payload.category is not None:
        inv.category = payload.category
    if payload.quantity_kg is not None:
        inv.quantity_kg = payload.quantity_kg
    if payload.price_per_kg is not None:
        inv.price_per_kg = payload.price_per_kg
    if payload.quality_grade is not None:
        inv.quality_grade = payload.quality_grade

    # Recompute total_value
    inv.total_value = Decimal(str(inv.quantity_kg)) * inv.price_per_kg

    return _to_schema(repo.update_dealer_inventory(db, inv))


def delete_dealer_inventory(db: Session, current_user: User, inventory_id: int) -> None:
    inv = _get_dealer_inventory_model(db, current_user, inventory_id)
    if inv.status != DealerInventoryStatus.available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only available inventory can be deleted",
        )
    repo.delete_dealer_inventory(db, inv)


def reserve_inventory(db: Session, current_user: User, inventory_id: int) -> DealerInventoryRead:
    inv = _get_dealer_inventory_model(db, current_user, inventory_id)
    if inv.status != DealerInventoryStatus.available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only available inventory can be reserved",
        )
    inv.status = DealerInventoryStatus.reserved
    return _to_schema(repo.update_dealer_inventory(db, inv))


def release_inventory(db: Session, current_user: User, inventory_id: int) -> DealerInventoryRead:
    inv = _get_dealer_inventory_model(db, current_user, inventory_id)
    if inv.status != DealerInventoryStatus.reserved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only reserved inventory can be released",
        )
    inv.status = DealerInventoryStatus.available
    return _to_schema(repo.update_dealer_inventory(db, inv))


def mark_inventory_sold(db: Session, current_user: User, inventory_id: int) -> DealerInventoryRead:
    inv = _get_dealer_inventory_model(db, current_user, inventory_id)
    if inv.status == DealerInventoryStatus.sold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory is already sold",
        )
    inv.status = DealerInventoryStatus.sold
    return _to_schema(repo.update_dealer_inventory(db, inv))
