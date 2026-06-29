from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.inventory import (
    DealerInventoryLotPageRead,
    DealerInventoryLotRead,
    EligiblePickupRead,
    InventoryLotArchiveRequest,
    InventoryLotArchiveRead,
    InventoryLotCreate,
    InventoryLotEventRead,
    InventoryLotPageRead,
    InventoryLotRead,
    InventoryLotUpdate,
    MaterialCategoryCreate,
    MaterialCategoryRead,
    PricingRuleCreate,
    PricingRuleRead,
    PricingRuleUpdate,
)
from app.services.inventory_marketplace import (
    activate_pricing_rule,
    archive_inventory_lot,
    create_inventory_lot,
    create_material_category,
    create_pricing_rule,
    deactivate_pricing_rule,
    get_inventory_lot_for_admin,
    get_inventory_lot_for_dealer,
    list_eligible_pickups_for_inventory,
    list_inventory_lot_events,
    list_inventory_lots_for_admin,
    list_inventory_lots_for_dealer,
    list_material_categories,
    list_pricing_rules,
    restore_inventory_lot,
    update_inventory_lot,
    update_pricing_rule,
)

# Two routers because this feature is consumed by two different roles under
# two different URL prefixes (/admin and /dealer). Each is mounted separately
# in app/api/router.py.
admin_router = APIRouter()
dealer_router = APIRouter()


# ─── Admin: Material categories ──────────────────────────────────────────────

@admin_router.post(
    "/material-categories",
    response_model=MaterialCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_material_category(
    payload: MaterialCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> MaterialCategoryRead:
    return create_material_category(db, current_user, payload)


@admin_router.get("/material-categories", response_model=list[MaterialCategoryRead])
def admin_list_material_categories(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[MaterialCategoryRead]:
    return list_material_categories(db, active_only=active_only)


# ─── Admin: Pricing rules ─────────────────────────────────────────────────────

@admin_router.get("/pricing-rules", response_model=list[PricingRuleRead])
def admin_list_pricing_rules(
    material_category_id: int | None = Query(default=None),
    city: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[PricingRuleRead]:
    return list_pricing_rules(
        db,
        material_category_id=material_category_id,
        city=city,
        is_active=is_active,
    )


@admin_router.post("/pricing-rules", response_model=PricingRuleRead, status_code=status.HTTP_201_CREATED)
def admin_create_pricing_rule(
    payload: PricingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> PricingRuleRead:
    return create_pricing_rule(db, current_user, payload)


@admin_router.patch("/pricing-rules/{pricing_rule_id}", response_model=PricingRuleRead)
def admin_update_pricing_rule(
    pricing_rule_id: int,
    payload: PricingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> PricingRuleRead:
    return update_pricing_rule(db, current_user, pricing_rule_id, payload)


@admin_router.post("/pricing-rules/{pricing_rule_id}/activate", response_model=PricingRuleRead)
def admin_activate_pricing_rule(
    pricing_rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> PricingRuleRead:
    return activate_pricing_rule(db, current_user, pricing_rule_id)


@admin_router.post("/pricing-rules/{pricing_rule_id}/deactivate", response_model=PricingRuleRead)
def admin_deactivate_pricing_rule(
    pricing_rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> PricingRuleRead:
    return deactivate_pricing_rule(db, current_user, pricing_rule_id)


# ─── Admin: Eligible pickups ──────────────────────────────────────────────────

@admin_router.get("/eligible-pickups", response_model=list[EligiblePickupRead])
def admin_list_eligible_pickups(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[EligiblePickupRead]:
    return list_eligible_pickups_for_inventory(db)


# ─── Admin: Inventory lots ────────────────────────────────────────────────────

@admin_router.get("/inventory-lots", response_model=InventoryLotPageRead)
def admin_list_inventory_lots(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    status_value: str | None = Query(default=None, alias="status"),
    city: str | None = Query(default=None),
    material_category_id: int | None = Query(default=None),
    visibility: str | None = Query(default=None),
    quality_grade: str | None = Query(default=None),
    archived: bool | None = Query(default=False),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> InventoryLotPageRead:
    return list_inventory_lots_for_admin(
        db,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        status_value=status_value,
        city=city,
        material_category_id=material_category_id,
        visibility=visibility,
        quality_grade=quality_grade,
        archived=archived,
        search=search,
    )


@admin_router.get("/inventory-lots/{lot_id}", response_model=InventoryLotRead)
def admin_get_inventory_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> InventoryLotRead:
    return get_inventory_lot_for_admin(db, lot_id)


@admin_router.post("/inventory-lots", response_model=InventoryLotRead, status_code=status.HTTP_201_CREATED)
def admin_create_inventory_lot(
    payload: InventoryLotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> InventoryLotRead:
    return create_inventory_lot(db, current_user, payload)


@admin_router.patch("/inventory-lots/{lot_id}", response_model=InventoryLotRead)
def admin_update_inventory_lot(
    lot_id: int,
    payload: InventoryLotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> InventoryLotRead:
    return update_inventory_lot(db, current_user, lot_id, payload)


@admin_router.post("/inventory-lots/{lot_id}/archive", response_model=InventoryLotArchiveRead)
def admin_archive_inventory_lot(
    lot_id: int,
    payload: InventoryLotArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> InventoryLotArchiveRead:
    return archive_inventory_lot(db, current_user, lot_id, payload)


@admin_router.post("/inventory-lots/{lot_id}/restore", response_model=InventoryLotArchiveRead)
def admin_restore_inventory_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> InventoryLotArchiveRead:
    return restore_inventory_lot(db, current_user, lot_id)


@admin_router.get("/inventory-lots/{lot_id}/events", response_model=list[InventoryLotEventRead])
def admin_list_inventory_lot_events(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> list[InventoryLotEventRead]:
    return list_inventory_lot_events(db, lot_id)


# ─── Dealer: Inventory browsing ───────────────────────────────────────────────

@dealer_router.get("/inventory-lots", response_model=DealerInventoryLotPageRead)
def dealer_list_inventory_lots(
    material_category_id: int | None = Query(default=None),
    city: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryLotPageRead:
    return list_inventory_lots_for_dealer(
        db,
        dealer=current_user,
        material_category_id=material_category_id,
        city=city,
        page=page,
        page_size=page_size,
    )


@dealer_router.get("/inventory-lots/{lot_id}", response_model=DealerInventoryLotRead)
def dealer_get_inventory_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryLotRead:
    return get_inventory_lot_for_dealer(db, current_user, lot_id)
