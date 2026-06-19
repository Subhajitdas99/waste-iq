from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.collector_assignment import CollectorAssignment
from app.models.dealer_profile import DealerProfile, DealerVerificationStatus
from app.models.inventory_lot import InventoryLot, InventoryLotStatus
from app.models.inventory_lot_event import InventoryLotEvent, InventoryLotEventType
from app.models.material_category import MaterialCategory
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.pricing_rule import PricingRule
from app.models.user import User, UserRole
from app.schemas.inventory import (
    DealerInventoryLotPageRead,
    DealerInventoryLotRead,
    EligiblePickupRead,
    InventoryLotArchiveRead,
    InventoryLotCreate,
    InventoryLotEventRead,
    InventoryLotRead,
    InventoryLotUpdate,
    MaterialCategoryRead,
    PricingRuleCreate,
    PricingRuleRead,
    PricingRuleUpdate,
)

MONEY_PLACES = Decimal("0.01")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_decimal(value: float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _money_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP))


def _normalize_city(value: str) -> str:
    return value.strip()


def _extract_city_from_address(address: str) -> str:
    parts = [part.strip() for part in address.split(",") if part.strip()]
    if len(parts) >= 2:
        return parts[-2] if len(parts[-1]) <= 10 and parts[-1].isdigit() else parts[-1]
    return "Kolkata"


def _inventory_lot_query(include_events: bool = False):
    statement = select(InventoryLot).options(
        selectinload(InventoryLot.material_category),
        selectinload(InventoryLot.citizen),
        selectinload(InventoryLot.collector),
        selectinload(InventoryLot.pricing_rule),
    )
    if include_events:
        statement = statement.options(selectinload(InventoryLot.events).selectinload(InventoryLotEvent.actor))
    return statement


def _pricing_rule_query():
    return select(PricingRule).options(selectinload(PricingRule.material_category))


def _serialize_category(category: MaterialCategory) -> MaterialCategoryRead:
    return MaterialCategoryRead.model_validate(category)


def _serialize_pricing_rule(rule: PricingRule) -> PricingRuleRead:
    return PricingRuleRead(
        id=rule.id,
        material_category_id=rule.material_category_id,
        material_category_name=rule.material_category.name,
        city=rule.city,
        unit_price_per_kg=_money_to_float(rule.unit_price_per_kg) or 0.0,
        currency_code=rule.currency_code,
        is_active=rule.is_active,
        effective_from=rule.effective_from,
        effective_to=rule.effective_to,
        created_by=rule.created_by,
        updated_by=rule.updated_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _serialize_inventory_lot(lot: InventoryLot) -> InventoryLotRead:
    return InventoryLotRead(
        id=lot.id,
        pickup_request_id=lot.pickup_request_id,
        citizen_id=lot.citizen_id,
        citizen_name=lot.citizen.name,
        collector_id=lot.collector_id,
        collector_name=lot.collector.name,
        material_category_id=lot.material_category_id,
        material_category_name=lot.material_category.name,
        material_description=lot.material_description,
        weight_kg=round(float(lot.weight_kg), 2),
        unit_price_per_kg_snapshot=_money_to_float(lot.unit_price_per_kg_snapshot) or 0.0,
        total_listed_amount=_money_to_float(lot.total_listed_amount) or 0.0,
        pricing_rule_id=lot.pricing_rule_id,
        source_city=lot.source_city,
        source_address_snapshot=lot.source_address_snapshot,
        status=lot.status.value,
        archived_at=lot.archived_at,
        created_by=lot.created_by,
        updated_by=lot.updated_by,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
    )


def _serialize_dealer_lot(lot: InventoryLot) -> DealerInventoryLotRead:
    return DealerInventoryLotRead(
        id=lot.id,
        material_category_id=lot.material_category_id,
        material_category_name=lot.material_category.name,
        material_description=lot.material_description,
        weight_kg=round(float(lot.weight_kg), 2),
        unit_price_per_kg_snapshot=_money_to_float(lot.unit_price_per_kg_snapshot) or 0.0,
        total_listed_amount=_money_to_float(lot.total_listed_amount) or 0.0,
        source_city=lot.source_city,
        status=lot.status.value,
        created_at=lot.created_at,
    )


def _serialize_inventory_event(event: InventoryLotEvent) -> InventoryLotEventRead:
    return InventoryLotEventRead(
        id=event.id,
        event_type=event.event_type.value,
        previous_status=event.previous_status.value if event.previous_status is not None else None,
        new_status=event.new_status.value if event.new_status is not None else None,
        actor_user_id=event.actor_user_id,
        actor_name=event.actor.name if event.actor is not None else None,
        event_notes=event.event_notes,
        metadata_json=event.metadata_json,
        created_at=event.created_at,
    )


def _get_category_or_404(db: Session, category_id: int) -> MaterialCategory:
    category = db.get(MaterialCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material category not found")
    return category


def _get_lot_or_404(db: Session, lot_id: int, include_events: bool = False) -> InventoryLot:
    lot = db.execute(_inventory_lot_query(include_events=include_events).where(InventoryLot.id == lot_id)).scalar_one_or_none()
    if lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory lot not found")
    return lot


def _get_pricing_rule_or_404(db: Session, pricing_rule_id: int) -> PricingRule:
    rule = db.execute(_pricing_rule_query().where(PricingRule.id == pricing_rule_id)).scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing rule not found")
    return rule


def _ensure_admin(user: User) -> None:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage inventory")


def _ensure_approved_dealer(db: Session, dealer: User) -> None:
    if dealer.role != UserRole.dealer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only dealers can browse inventory")

    profile = db.execute(select(DealerProfile).where(DealerProfile.user_id == dealer.id)).scalar_one_or_none()
    if profile is None or profile.verification_status != DealerVerificationStatus.approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dealer approval is required to browse inventory")


def _get_active_pricing_rule(db: Session, material_category_id: int, city: str) -> PricingRule:
    now = _utc_now()
    rules = (
        db.execute(
            _pricing_rule_query()
            .where(
                PricingRule.material_category_id == material_category_id,
                PricingRule.city == city,
                PricingRule.is_active.is_(True),
                PricingRule.effective_from <= now,
                (PricingRule.effective_to.is_(None) | (PricingRule.effective_to >= now)),
            )
            .order_by(PricingRule.effective_from.desc(), PricingRule.created_at.desc())
        )
        .scalars()
        .all()
    )
    if not rules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active pricing rule exists for the selected material category and city",
        )
    return rules[0]


def _ensure_no_active_pricing_conflict(
    db: Session,
    *,
    material_category_id: int,
    city: str,
    exclude_rule_id: int | None = None,
) -> None:
    statement = select(PricingRule).where(
        PricingRule.material_category_id == material_category_id,
        PricingRule.city == city,
        PricingRule.is_active.is_(True),
    )
    if exclude_rule_id is not None:
        statement = statement.where(PricingRule.id != exclude_rule_id)

    conflicting_rule = db.execute(statement.limit(1)).scalar_one_or_none()
    if conflicting_rule is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active pricing rule already exists for this material category and city",
        )


def _create_lot_event(
    db: Session,
    lot: InventoryLot,
    *,
    event_type: InventoryLotEventType,
    actor: User | None,
    previous_status: InventoryLotStatus | None = None,
    new_status: InventoryLotStatus | None = None,
    event_notes: str | None = None,
    metadata_json: dict | None = None,
) -> None:
    db.add(
        InventoryLotEvent(
            inventory_lot_id=lot.id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            actor_user_id=actor.id if actor is not None else None,
            event_notes=event_notes,
            metadata_json=metadata_json,
        )
    )


def list_material_categories(db: Session, *, active_only: bool = True) -> list[MaterialCategoryRead]:
    statement = select(MaterialCategory)
    if active_only:
        statement = statement.where(MaterialCategory.is_active.is_(True))
    statement = statement.order_by(MaterialCategory.display_order.asc(), MaterialCategory.name.asc())
    categories = db.execute(statement).scalars().all()
    return [_serialize_category(category) for category in categories]


def list_pricing_rules(
    db: Session,
    *,
    material_category_id: int | None = None,
    city: str | None = None,
    is_active: bool | None = None,
) -> list[PricingRuleRead]:
    statement = _pricing_rule_query().order_by(PricingRule.created_at.desc())
    if material_category_id is not None:
        statement = statement.where(PricingRule.material_category_id == material_category_id)
    if city is not None:
        statement = statement.where(PricingRule.city == city.strip())
    if is_active is not None:
        statement = statement.where(PricingRule.is_active.is_(is_active))
    rules = db.execute(statement).scalars().all()
    return [_serialize_pricing_rule(rule) for rule in rules]


def create_pricing_rule(db: Session, admin: User, payload: PricingRuleCreate) -> PricingRuleRead:
    _ensure_admin(admin)
    category = _get_category_or_404(db, payload.material_category_id)
    if not category.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive material categories cannot be priced")
    if payload.effective_to is not None and payload.effective_to < payload.effective_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="effective_to cannot be earlier than effective_from")

    city = _normalize_city(payload.city)
    if payload.is_active:
        _ensure_no_active_pricing_conflict(db, material_category_id=payload.material_category_id, city=city)

    rule = PricingRule(
        material_category_id=payload.material_category_id,
        city=city,
        unit_price_per_kg=_to_decimal(payload.unit_price_per_kg),
        currency_code=payload.currency_code.upper(),
        is_active=payload.is_active,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(rule)
    db.commit()
    rule = _get_pricing_rule_or_404(db, rule.id)
    return _serialize_pricing_rule(rule)


def update_pricing_rule(db: Session, admin: User, pricing_rule_id: int, payload: PricingRuleUpdate) -> PricingRuleRead:
    _ensure_admin(admin)
    rule = _get_pricing_rule_or_404(db, pricing_rule_id)
    update_data = payload.model_dump(exclude_unset=True, mode="json")
    if not update_data:
        return _serialize_pricing_rule(rule)

    next_is_active = update_data.get("is_active", rule.is_active)
    if "effective_to" in update_data and update_data["effective_to"] is not None:
        effective_from = update_data.get("effective_from", rule.effective_from)
        if update_data["effective_to"] < effective_from:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="effective_to cannot be earlier than effective_from")
    if next_is_active:
        _ensure_no_active_pricing_conflict(
            db,
            material_category_id=rule.material_category_id,
            city=rule.city,
            exclude_rule_id=rule.id,
        )

    for field, value in update_data.items():
        if field == "unit_price_per_kg":
            setattr(rule, field, _to_decimal(value))
        elif field == "currency_code" and value is not None:
            setattr(rule, field, value.upper())
        else:
            setattr(rule, field, value)

    rule.updated_by = admin.id
    db.commit()
    rule = _get_pricing_rule_or_404(db, rule.id)
    return _serialize_pricing_rule(rule)


def activate_pricing_rule(db: Session, admin: User, pricing_rule_id: int) -> PricingRuleRead:
    _ensure_admin(admin)
    rule = _get_pricing_rule_or_404(db, pricing_rule_id)
    _ensure_no_active_pricing_conflict(
        db,
        material_category_id=rule.material_category_id,
        city=rule.city,
        exclude_rule_id=rule.id,
    )
    rule.is_active = True
    rule.updated_by = admin.id
    db.commit()
    rule = _get_pricing_rule_or_404(db, rule.id)
    return _serialize_pricing_rule(rule)


def deactivate_pricing_rule(db: Session, admin: User, pricing_rule_id: int) -> PricingRuleRead:
    _ensure_admin(admin)
    rule = _get_pricing_rule_or_404(db, pricing_rule_id)
    rule.is_active = False
    rule.updated_by = admin.id
    db.commit()
    rule = _get_pricing_rule_or_404(db, rule.id)
    return _serialize_pricing_rule(rule)


def list_eligible_pickups_for_inventory(db: Session) -> list[EligiblePickupRead]:
    statement = (
        select(PickupRequest)
        .options(
            selectinload(PickupRequest.citizen),
            selectinload(PickupRequest.assignment).selectinload(CollectorAssignment.collector),
            selectinload(PickupRequest.inventory_lot),
        )
        .where(PickupRequest.status == PickupStatus.completed)
        .order_by(PickupRequest.created_at.desc())
    )
    pickup_requests = db.execute(statement).scalars().all()

    eligible_items: list[EligiblePickupRead] = []
    for pickup in pickup_requests:
        if pickup.assignment is None or pickup.assignment.collector is None:
            continue
        if pickup.assignment.weight_kg is None or pickup.assignment.weight_kg <= 0:
            continue
        if pickup.inventory_lot is not None:
            continue

        eligible_items.append(
            EligiblePickupRead(
                pickup_request_id=pickup.id,
                citizen_id=pickup.user_id,
                citizen_name=pickup.citizen.name,
                collector_id=pickup.assignment.collector_id,
                collector_name=pickup.assignment.collector.name,
                waste_type=pickup.waste_type,
                material_description=pickup.waste_type,
                weight_kg=round(float(pickup.assignment.weight_kg), 2),
                source_city=_extract_city_from_address(pickup.address),
                completed_at=pickup.assignment.completed_at,
            )
        )

    return eligible_items


def _get_eligible_pickup_or_400(db: Session, pickup_request_id: int) -> PickupRequest:
    pickup = (
        db.execute(
            select(PickupRequest)
            .options(
                selectinload(PickupRequest.assignment),
                selectinload(PickupRequest.citizen),
                selectinload(PickupRequest.inventory_lot),
            )
            .where(PickupRequest.id == pickup_request_id)
        )
        .scalar_one_or_none()
    )
    if pickup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found")
    if pickup.status != PickupStatus.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup request is not eligible for inventory")
    if pickup.assignment is None or pickup.assignment.weight_kg is None or pickup.assignment.weight_kg <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pickup request does not have a valid completed weight")
    if pickup.inventory_lot is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An inventory lot already exists for this pickup")
    return pickup


def create_inventory_lot(db: Session, admin: User, payload: InventoryLotCreate) -> InventoryLotRead:
    _ensure_admin(admin)
    pickup = _get_eligible_pickup_or_400(db, payload.pickup_request_id)
    category = _get_category_or_404(db, payload.material_category_id)
    if not category.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive material categories cannot be used for inventory")

    try:
        lot_status = InventoryLotStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid inventory lot status") from exc

    source_city = _extract_city_from_address(pickup.address)
    pricing_rule = _get_active_pricing_rule(db, payload.material_category_id, source_city)
    weight_kg = round(float(pickup.assignment.weight_kg or 0), 2)
    unit_price = _to_decimal(pricing_rule.unit_price_per_kg)
    total_amount = _to_decimal(Decimal(str(weight_kg)) * unit_price)

    lot = InventoryLot(
        pickup_request_id=pickup.id,
        citizen_id=pickup.user_id,
        collector_id=pickup.assignment.collector_id,
        material_category_id=payload.material_category_id,
        material_description=payload.material_description or pickup.waste_type,
        weight_kg=weight_kg,
        unit_price_per_kg_snapshot=unit_price,
        total_listed_amount=total_amount,
        pricing_rule_id=pricing_rule.id,
        source_city=source_city,
        source_address_snapshot=pickup.address,
        status=lot_status,
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(lot)
    db.flush()
    _create_lot_event(
        db,
        lot,
        event_type=InventoryLotEventType.created,
        actor=admin,
        new_status=lot.status,
        event_notes="Inventory lot created from completed pickup.",
        metadata_json={
            "pickup_request_id": pickup.id,
            "pricing_rule_id": pricing_rule.id,
            "weight_kg": weight_kg,
        },
    )
    db.commit()
    lot = _get_lot_or_404(db, lot.id)
    return _serialize_inventory_lot(lot)


def list_inventory_lots_for_admin(
    db: Session,
    *,
    status_value: str | None = None,
    city: str | None = None,
    material_category_id: int | None = None,
    archived: bool | None = None,
) -> list[InventoryLotRead]:
    statement = _inventory_lot_query().order_by(InventoryLot.created_at.desc())
    if status_value is not None:
        try:
            lot_status = InventoryLotStatus(status_value)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid inventory lot status") from exc
        statement = statement.where(InventoryLot.status == lot_status)
    if city is not None:
        statement = statement.where(InventoryLot.source_city == city.strip())
    if material_category_id is not None:
        statement = statement.where(InventoryLot.material_category_id == material_category_id)
    if archived is True:
        statement = statement.where(InventoryLot.archived_at.is_not(None))
    elif archived is False:
        statement = statement.where(InventoryLot.archived_at.is_(None))

    lots = db.execute(statement).scalars().all()
    return [_serialize_inventory_lot(lot) for lot in lots]


def get_inventory_lot_for_admin(db: Session, lot_id: int) -> InventoryLotRead:
    return _serialize_inventory_lot(_get_lot_or_404(db, lot_id))


def update_inventory_lot(db: Session, admin: User, lot_id: int, payload: InventoryLotUpdate) -> InventoryLotRead:
    _ensure_admin(admin)
    lot = _get_lot_or_404(db, lot_id)
    update_data = payload.model_dump(exclude_unset=True, mode="json")
    if not update_data:
        return _serialize_inventory_lot(lot)

    previous_status = lot.status
    event_notes: list[str] = []
    metadata: dict[str, object] = {}

    if "material_category_id" in update_data and update_data["material_category_id"] != lot.material_category_id:
        if lot.archived_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archived lots cannot change material category")
        if lot.status == InventoryLotStatus.sold:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sold lots cannot change material category")

        category = _get_category_or_404(db, update_data["material_category_id"])
        if not category.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive material categories cannot be used for inventory")

        pricing_rule = _get_active_pricing_rule(db, category.id, lot.source_city)
        unit_price = _to_decimal(pricing_rule.unit_price_per_kg)
        total_amount = _to_decimal(Decimal(str(lot.weight_kg)) * unit_price)

        lot.material_category_id = category.id
        lot.pricing_rule_id = pricing_rule.id
        lot.unit_price_per_kg_snapshot = unit_price
        lot.total_listed_amount = total_amount
        event_notes.append("Material category updated and pricing snapshot recalculated.")
        metadata["material_category_id"] = category.id
        metadata["pricing_rule_id"] = pricing_rule.id

    if "material_description" in update_data:
        lot.material_description = update_data["material_description"]
        event_notes.append("Material description updated.")

    if "status" in update_data:
        try:
            lot.status = InventoryLotStatus(update_data["status"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid inventory lot status") from exc
        if lot.status != previous_status:
            event_notes.append(f"Status changed from {previous_status.value} to {lot.status.value}.")

    lot.updated_by = admin.id

    event_type = InventoryLotEventType.updated
    next_status: InventoryLotStatus | None = None
    previous_status_for_event: InventoryLotStatus | None = None
    if lot.status != previous_status:
        event_type = InventoryLotEventType.status_changed
        previous_status_for_event = previous_status
        next_status = lot.status

    _create_lot_event(
        db,
        lot,
        event_type=event_type,
        actor=admin,
        previous_status=previous_status_for_event,
        new_status=next_status,
        event_notes=" ".join(event_notes) if event_notes else "Inventory lot updated.",
        metadata_json=metadata or None,
    )
    db.commit()
    lot = _get_lot_or_404(db, lot.id)
    return _serialize_inventory_lot(lot)


def archive_inventory_lot(db: Session, admin: User, lot_id: int) -> InventoryLotArchiveRead:
    _ensure_admin(admin)
    lot = _get_lot_or_404(db, lot_id)
    if lot.archived_at is None:
        lot.archived_at = _utc_now()
        lot.updated_by = admin.id
        _create_lot_event(
            db,
            lot,
            event_type=InventoryLotEventType.archived,
            actor=admin,
            previous_status=lot.status,
            new_status=lot.status,
            event_notes="Inventory lot archived.",
        )
        db.commit()
        lot = _get_lot_or_404(db, lot.id)

    return InventoryLotArchiveRead(id=lot.id, status=lot.status.value, archived_at=lot.archived_at)


def list_inventory_lot_events(db: Session, lot_id: int) -> list[InventoryLotEventRead]:
    lot = _get_lot_or_404(db, lot_id, include_events=True)
    return [_serialize_inventory_event(event) for event in lot.events]


def list_inventory_lots_for_dealer(
    db: Session,
    *,
    dealer: User,
    material_category_id: int | None = None,
    city: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> DealerInventoryLotPageRead:
    _ensure_approved_dealer(db, dealer)
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page must be at least 1")
    if page_size < 1 or page_size > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page_size must be between 1 and 50")

    filters = [
        InventoryLot.status == InventoryLotStatus.available,
        InventoryLot.archived_at.is_(None),
    ]
    if material_category_id is not None:
        filters.append(InventoryLot.material_category_id == material_category_id)
    if city is not None:
        filters.append(InventoryLot.source_city == city.strip())

    total_items = db.scalar(select(func.count(InventoryLot.id)).where(*filters)) or 0
    total_pages = ceil(total_items / page_size) if total_items else 0

    statement = (
        _inventory_lot_query()
        .where(*filters)
        .order_by(InventoryLot.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    lots = db.execute(statement).scalars().all()
    return DealerInventoryLotPageRead(
        items=[_serialize_dealer_lot(lot) for lot in lots],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


def get_inventory_lot_for_dealer(db: Session, dealer: User, lot_id: int) -> DealerInventoryLotRead:
    _ensure_approved_dealer(db, dealer)
    lot = db.execute(
        _inventory_lot_query().where(
            InventoryLot.id == lot_id,
            InventoryLot.status == InventoryLotStatus.available,
            InventoryLot.archived_at.is_(None),
        )
    ).scalar_one_or_none()
    if lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory lot not found")
    return _serialize_dealer_lot(lot)
