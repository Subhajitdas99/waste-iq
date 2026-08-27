from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles, require_verified_roles
from app.models.user import User
from app.schemas.marketplace import (
    MarketplaceInventoryPageRead,
    MarketplaceInventoryRead,
    MarketplaceOrderDetailRead,
    MarketplaceOrderPageRead,
    MarketplaceTransactionPageRead,
)
from app.services import marketplace

router = APIRouter()


@router.get("/inventory", response_model=MarketplaceInventoryPageRead)
def marketplace_list_inventory(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    material_category_id: int | None = Query(default=None),
    city: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> MarketplaceInventoryPageRead:
    return marketplace.list_marketplace_inventory(
        db,
        dealer=current_user,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        material_category_id=material_category_id,
        city=city,
        search=search,
    )


@router.get("/inventory/{lot_id}", response_model=MarketplaceInventoryRead)
def marketplace_get_inventory(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> MarketplaceInventoryRead:
    return marketplace.get_marketplace_inventory(db, current_user, lot_id)


@router.post(
    "/inventory/{lot_id}/reserve",
    response_model=MarketplaceInventoryRead,
    status_code=status.HTTP_200_OK,
)
def marketplace_reserve_inventory(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_roles("dealer")),
) -> MarketplaceInventoryRead:
    return marketplace.reserve_marketplace_inventory(db, current_user, lot_id)


@router.post(
    "/inventory/{lot_id}/cancel-reservation",
    response_model=MarketplaceInventoryRead,
    status_code=status.HTTP_200_OK,
)
def marketplace_cancel_reservation(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_roles("dealer")),
) -> MarketplaceInventoryRead:
    return marketplace.cancel_marketplace_reservation(db, current_user, lot_id)


@router.post(
    "/inventory/{lot_id}/purchase",
    response_model=MarketplaceOrderDetailRead,
    status_code=status.HTTP_201_CREATED,
)
def marketplace_purchase_inventory(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_roles("dealer")),
) -> MarketplaceOrderDetailRead:
    return marketplace.purchase_marketplace_inventory(db, current_user, lot_id)


@router.get("/orders", response_model=MarketplaceOrderPageRead)
def marketplace_list_orders(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> MarketplaceOrderPageRead:
    return marketplace.list_marketplace_orders(
        db, dealer=current_user, page=page, page_size=page_size
    )


@router.get("/orders/{order_id}", response_model=MarketplaceOrderDetailRead)
def marketplace_get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> MarketplaceOrderDetailRead:
    return marketplace.get_marketplace_order(db, current_user, order_id)


@router.get("/transactions", response_model=MarketplaceTransactionPageRead)
def marketplace_list_transactions(
    page: int = Query(default=1),
    page_size: int = Query(default=20),
    transaction_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> MarketplaceTransactionPageRead:
    return marketplace.list_marketplace_transactions(
        db,
        dealer=current_user,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type,
    )
