from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MarketplaceInventoryRead(BaseModel):
    id: int
    lot_number: str
    material_category_id: int
    material_category_name: str
    material_description: str | None
    weight_kg: float
    unit_price_per_kg_snapshot: float
    total_listed_amount: float
    currency_code: str | None
    source_city: str
    quality_grade: str | None
    status: str
    seller_name: str | None
    reserved_at: datetime | None
    reservation_expires_at: datetime | None
    is_reserved_by_me: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketplaceInventoryPageRead(BaseModel):
    items: list[MarketplaceInventoryRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class MarketplaceTransactionRead(BaseModel):
    id: int
    order_id: int | None
    inventory_lot_id: int
    lot_number: str
    material_category_name: str
    dealer_id: int
    dealer_name: str | None
    transaction_type: str
    status: str
    quantity_kg: float
    unit_price_per_kg_snapshot: float
    total_amount: float
    currency_code: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketplaceTransactionPageRead(BaseModel):
    items: list[MarketplaceTransactionRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class MarketplaceOrderRead(BaseModel):
    id: int
    order_number: str
    inventory_lot_id: int
    lot_number: str
    material_category_id: int
    material_category_name: str
    material_description: str | None
    dealer_id: int
    dealer_name: str | None
    quantity_kg: float
    unit_price_per_kg_snapshot: float
    total_amount: float
    currency_code: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketplaceOrderDetailRead(MarketplaceOrderRead):
    transactions: list[MarketplaceTransactionRead] = []


class MarketplaceOrderPageRead(BaseModel):
    items: list[MarketplaceOrderRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int
