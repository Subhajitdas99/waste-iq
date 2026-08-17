from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.inventory_lot import InventoryLot, InventoryLotStatus, InventoryLotVisibility
from app.models.inventory_lot_event import InventoryLotEventType
from app.models.marketplace_order import MarketplaceOrder
from app.models.marketplace_transaction import (
    MarketplaceTransaction,
    MarketplaceTransactionStatus,
    MarketplaceTransactionType,
)
from app.models.user import User
from app.repositories import marketplace as repo
from app.schemas.marketplace import (
    MarketplaceInventoryPageRead,
    MarketplaceInventoryRead,
    MarketplaceOrderDetailRead,
    MarketplaceOrderPageRead,
    MarketplaceOrderRead,
    MarketplaceTransactionPageRead,
    MarketplaceTransactionRead,
)
from app.services.dealer_approval import ensure_approved_dealer
from app.services.inventory_marketplace import (
    commit_or_rollback,
    create_lot_event,
    money_to_float,
    release_expired_reservations,
    reserve_inventory_lot,
    to_decimal,
    utc_now,
)
from app.services.notifications import NotificationDispatcher

PAGE_SIZE_MAX = 50
_dispatcher = NotificationDispatcher()


def _validate_pagination(page: int, page_size: int) -> None:
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="page must be at least 1"
        )
    if page_size < 1 or page_size > PAGE_SIZE_MAX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"page_size must be between 1 and {PAGE_SIZE_MAX}",
        )


def _as_naive_utc(value: datetime) -> datetime:
    """Normalize to naive UTC so comparisons work on both SQLite and PostgreSQL."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _currency_code_for_lot(lot: InventoryLot) -> str:
    return lot.pricing_rule.currency_code if lot.pricing_rule is not None else "INR"


def _serialize_inventory(lot: InventoryLot, dealer_id: int) -> MarketplaceInventoryRead:
    is_reserved_by_me = (
        lot.status == InventoryLotStatus.reserved and lot.reserved_by_dealer_id == dealer_id
    )
    return MarketplaceInventoryRead(
        id=lot.id,
        lot_number=lot.lot_number,
        material_category_id=lot.material_category_id,
        material_category_name=lot.material_category.name,
        material_description=lot.material_description,
        weight_kg=round(float(lot.weight_kg), 2),
        unit_price_per_kg_snapshot=money_to_float(lot.unit_price_per_kg_snapshot) or 0.0,
        total_listed_amount=money_to_float(lot.total_listed_amount) or 0.0,
        currency_code=_currency_code_for_lot(lot),
        source_city=lot.source_city,
        quality_grade=lot.quality_grade,
        status=lot.status.value,
        seller_name=lot.citizen.name if lot.citizen is not None else None,
        reserved_at=lot.reserved_at,
        reservation_expires_at=lot.reservation_expires_at,
        is_reserved_by_me=is_reserved_by_me,
        created_at=lot.created_at,
    )


def _serialize_transaction(transaction: MarketplaceTransaction) -> MarketplaceTransactionRead:
    lot = transaction.inventory_lot
    return MarketplaceTransactionRead(
        id=transaction.id,
        order_id=transaction.order_id,
        inventory_lot_id=transaction.inventory_lot_id,
        lot_number=lot.lot_number if lot is not None else "",
        material_category_name=(
            lot.material_category.name
            if lot is not None and lot.material_category is not None
            else ""
        ),
        dealer_id=transaction.dealer_id,
        dealer_name=transaction.dealer.name if transaction.dealer is not None else None,
        transaction_type=transaction.transaction_type.value,
        status=transaction.status.value,
        quantity_kg=round(float(transaction.quantity_kg), 2),
        unit_price_per_kg_snapshot=money_to_float(transaction.unit_price_per_kg_snapshot) or 0.0,
        total_amount=money_to_float(transaction.total_amount) or 0.0,
        currency_code=transaction.currency_code,
        created_at=transaction.created_at,
    )


def _serialize_order(order: MarketplaceOrder) -> MarketplaceOrderRead:
    lot = order.inventory_lot
    return MarketplaceOrderRead(
        id=order.id,
        order_number=order.order_number,
        inventory_lot_id=order.inventory_lot_id,
        lot_number=lot.lot_number if lot is not None else "",
        material_category_id=lot.material_category_id if lot is not None else 0,
        material_category_name=(
            lot.material_category.name
            if lot is not None and lot.material_category is not None
            else ""
        ),
        material_description=lot.material_description if lot is not None else None,
        dealer_id=order.dealer_id,
        dealer_name=order.dealer.name if order.dealer is not None else None,
        quantity_kg=round(float(order.quantity_kg), 2),
        unit_price_per_kg_snapshot=money_to_float(order.unit_price_per_kg_snapshot) or 0.0,
        total_amount=money_to_float(order.total_amount) or 0.0,
        currency_code=order.currency_code,
        status=order.status.value,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _serialize_order_detail(
    order: MarketplaceOrder, transactions: list[MarketplaceTransaction]
) -> MarketplaceOrderDetailRead:
    detail = MarketplaceOrderDetailRead(**_serialize_order(order).model_dump())
    detail.transactions = [_serialize_transaction(transaction) for transaction in transactions]
    return detail


def _get_visible_lot_or_404(db: Session, lot_id: int) -> InventoryLot:
    lot = repo.get_lot_by_id(db, lot_id)
    if (
        lot is None
        or lot.visibility != InventoryLotVisibility.visible
        or lot.archived_at is not None
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory lot not found")
    return lot


def list_marketplace_inventory(
    db: Session,
    *,
    dealer: User,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    material_category_id: int | None = None,
    city: str | None = None,
    search: str | None = None,
) -> MarketplaceInventoryPageRead:
    ensure_approved_dealer(db, dealer)
    release_expired_reservations(db)
    _validate_pagination(page, page_size)
    if sort_by not in repo.SORTABLE_INVENTORY_COLUMNS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort_by value")
    if sort_order not in {"asc", "desc"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort_order value"
        )

    items, total_items, total_pages = repo.list_visible_lots(
        db,
        dealer_id=dealer.id,
        material_category_id=material_category_id,
        city=city,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return MarketplaceInventoryPageRead(
        items=[_serialize_inventory(lot, dealer.id) for lot in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


def get_marketplace_inventory(db: Session, dealer: User, lot_id: int) -> MarketplaceInventoryRead:
    ensure_approved_dealer(db, dealer)
    release_expired_reservations(db)
    lot = _get_visible_lot_or_404(db, lot_id)
    if lot.status == InventoryLotStatus.sold:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory lot not found")
    if lot.status == InventoryLotStatus.reserved and lot.reserved_by_dealer_id != dealer.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory lot not found")
    return _serialize_inventory(lot, dealer.id)


def reserve_marketplace_inventory(
    db: Session, dealer: User, lot_id: int
) -> MarketplaceInventoryRead:
    lot = reserve_inventory_lot(db, dealer, lot_id)
    return _serialize_inventory(lot, dealer.id)


def cancel_marketplace_reservation(
    db: Session, dealer: User, lot_id: int
) -> MarketplaceInventoryRead:
    ensure_approved_dealer(db, dealer)

    with commit_or_rollback(db):
        lot = repo.get_lot_for_update(db, lot_id)
        if (
            lot is None
            or lot.visibility != InventoryLotVisibility.visible
            or lot.archived_at is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Inventory lot not found"
            )
        if lot.status != InventoryLotStatus.reserved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inventory lot is not currently reserved",
            )
        if lot.reserved_by_dealer_id != dealer.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reservation is held by another dealer",
            )

        previous_reserved_at = lot.reserved_at
        previous_expires_at = lot.reservation_expires_at
        lot.status = InventoryLotStatus.available
        lot.reserved_by_dealer_id = None
        lot.reserved_at = None
        lot.reservation_expires_at = None
        lot.updated_by = dealer.id
        create_lot_event(
            db,
            lot,
            event_type=InventoryLotEventType.reservation_cancelled,
            actor=dealer,
            previous_status=InventoryLotStatus.reserved,
            new_status=InventoryLotStatus.available,
            event_notes="Dealer reservation cancelled.",
            metadata_json={
                "reserved_at": (
                    previous_reserved_at.isoformat() if previous_reserved_at is not None else None
                ),
                "reservation_expires_at": (
                    previous_expires_at.isoformat() if previous_expires_at is not None else None
                ),
            },
        )
        repo.create_transaction(
            db,
            dealer_id=dealer.id,
            inventory_lot_id=lot.id,
            order_id=None,
            transaction_type=MarketplaceTransactionType.cancellation,
            status=MarketplaceTransactionStatus.cancelled,
            quantity_kg=round(float(lot.weight_kg), 2),
            unit_price_per_kg_snapshot=to_decimal(lot.unit_price_per_kg_snapshot),
            total_amount=to_decimal(lot.total_listed_amount),
            currency_code=_currency_code_for_lot(lot),
        )
        _dispatcher.notify_reservation_cancelled(db, lot)

    lot = _get_visible_lot_or_404(db, lot_id)
    return _serialize_inventory(lot, dealer.id)


def purchase_marketplace_inventory(
    db: Session, dealer: User, lot_id: int
) -> MarketplaceOrderDetailRead:
    ensure_approved_dealer(db, dealer)
    now: datetime = _as_naive_utc(utc_now())

    try:
        with commit_or_rollback(db):
            lot = repo.get_lot_for_update(db, lot_id)
            if (
                lot is None
                or lot.visibility != InventoryLotVisibility.visible
                or lot.archived_at is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Inventory lot not found"
                )
            if lot.status == InventoryLotStatus.sold:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inventory lot is already sold",
                )
            if lot.status != InventoryLotStatus.reserved:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inventory lot must be reserved before it can be purchased",
                )
            if lot.reserved_by_dealer_id != dealer.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inventory lot is reserved by another dealer",
                )
            if (
                lot.reservation_expires_at is not None
                and _as_naive_utc(lot.reservation_expires_at) < now
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inventory lot reservation has expired",
                )

            order = repo.create_order(
                db,
                inventory_lot_id=lot.id,
                dealer_id=dealer.id,
                quantity_kg=round(float(lot.weight_kg), 2),
                unit_price_per_kg_snapshot=to_decimal(lot.unit_price_per_kg_snapshot),
                total_amount=to_decimal(lot.total_listed_amount),
                currency_code=_currency_code_for_lot(lot),
            )
            repo.create_transaction(
                db,
                dealer_id=dealer.id,
                inventory_lot_id=lot.id,
                order_id=order.id,
                transaction_type=MarketplaceTransactionType.purchase,
                status=MarketplaceTransactionStatus.completed,
                quantity_kg=round(float(lot.weight_kg), 2),
                unit_price_per_kg_snapshot=to_decimal(lot.unit_price_per_kg_snapshot),
                total_amount=to_decimal(lot.total_listed_amount),
                currency_code=_currency_code_for_lot(lot),
            )
            lot.status = InventoryLotStatus.sold
            lot.reserved_by_dealer_id = None
            lot.reserved_at = None
            lot.reservation_expires_at = None
            lot.updated_by = dealer.id
            create_lot_event(
                db,
                lot,
                event_type=InventoryLotEventType.status_changed,
                actor=dealer,
                previous_status=InventoryLotStatus.reserved,
                new_status=InventoryLotStatus.sold,
                event_notes="Inventory lot purchased by approved dealer.",
                metadata_json={
                    "order_id": order.id,
                    "order_number": order.order_number,
                },
            )
            _dispatcher.notify_inventory_purchased(db, lot, order)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory lot purchase has already been recorded",
        ) from exc

    created_order = repo.get_order_by_id(db, order.id)
    if created_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    transactions = repo.list_transactions_by_lot(db, lot_id)
    return _serialize_order_detail(created_order, list(transactions))


def list_marketplace_orders(
    db: Session,
    *,
    dealer: User,
    page: int = 1,
    page_size: int = 20,
) -> MarketplaceOrderPageRead:
    ensure_approved_dealer(db, dealer)
    _validate_pagination(page, page_size)
    items, total_items, total_pages = repo.list_orders(
        db, dealer_id=dealer.id, page=page, page_size=page_size
    )
    return MarketplaceOrderPageRead(
        items=[_serialize_order(order) for order in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


def get_marketplace_order(db: Session, dealer: User, order_id: int) -> MarketplaceOrderDetailRead:
    ensure_approved_dealer(db, dealer)
    order = repo.get_order_by_id(db, order_id)
    if order is None or order.dealer_id != dealer.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    transactions = repo.list_transactions_by_lot(db, order.inventory_lot_id)
    return _serialize_order_detail(order, list(transactions))


def list_marketplace_transactions(
    db: Session,
    *,
    dealer: User,
    page: int = 1,
    page_size: int = 20,
    transaction_type: str | None = None,
) -> MarketplaceTransactionPageRead:
    ensure_approved_dealer(db, dealer)
    _validate_pagination(page, page_size)
    if transaction_type is not None:
        try:
            MarketplaceTransactionType(transaction_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid transaction type"
            ) from exc

    items, total_items, total_pages = repo.list_transactions(
        db,
        dealer_id=dealer.id,
        transaction_type=transaction_type,
        page=page,
        page_size=page_size,
    )
    return MarketplaceTransactionPageRead(
        items=[_serialize_transaction(transaction) for transaction in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
