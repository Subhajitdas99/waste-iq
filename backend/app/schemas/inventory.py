from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MaterialCategoryCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)

    model_config = ConfigDict(str_strip_whitespace=True)


class MaterialCategoryRead(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PricingRuleCreate(BaseModel):
    material_category_id: int
    city: str = Field(min_length=2, max_length=100)
    unit_price_per_kg: float = Field(ge=0)
    currency_code: str = Field(default="INR", min_length=3, max_length=3)
    is_active: bool = True
    effective_from: datetime
    effective_to: datetime | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PricingRuleUpdate(BaseModel):
    unit_price_per_kg: float | None = Field(default=None, ge=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PricingRuleRead(BaseModel):
    id: int
    material_category_id: int
    material_category_name: str
    city: str
    unit_price_per_kg: float
    currency_code: str
    is_active: bool
    effective_from: datetime
    effective_to: datetime | None
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EligiblePickupRead(BaseModel):
    pickup_request_id: int
    citizen_id: int
    citizen_name: str
    collector_id: int
    collector_name: str
    waste_type: str
    material_description: str | None
    weight_kg: float
    source_city: str
    completed_at: datetime | None


class InventoryLotCreate(BaseModel):
    pickup_request_id: int
    material_category_id: int
    material_description: str | None = Field(default=None, max_length=1000)
    status: str = Field(default="available")

    model_config = ConfigDict(str_strip_whitespace=True)


class InventoryLotUpdate(BaseModel):
    quality_grade: str | None = Field(default=None, max_length=30)
    admin_notes: str | None = Field(default=None, max_length=2000)
    visibility: str | None = None
    archive_reason: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class InventoryLotArchiveRead(BaseModel):
    id: int
    lot_number: str
    status: str
    visibility: str
    archived_at: datetime | None
    archive_reason: str | None


class InventoryLotArchiveRequest(BaseModel):
    archive_reason: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(str_strip_whitespace=True)


class InventoryLotPageRead(BaseModel):
    items: list["InventoryLotRead"]
    page: int
    page_size: int
    total: int
    total_pages: int


class InventoryLotEventRead(BaseModel):
    id: int
    event_type: str
    previous_status: str | None
    new_status: str | None
    actor_user_id: int | None
    actor_name: str | None
    event_notes: str | None
    metadata_json: dict | None
    created_at: datetime


class InventoryLotRead(BaseModel):
    id: int
    lot_number: str
    pickup_request_id: int
    citizen_id: int
    citizen_name: str
    collector_id: int
    collector_name: str
    material_category_id: int
    material_category_name: str
    material_description: str | None
    weight_kg: float
    unit_price_per_kg_snapshot: float
    total_listed_amount: float
    pricing_rule_id: int | None
    source_city: str
    source_address_snapshot: str | None
    quality_grade: str | None
    admin_notes: str | None
    visibility: str
    status: str
    archived_at: datetime | None
    archive_reason: str | None
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealerInventoryLotRead(BaseModel):
    id: int
    material_category_id: int
    material_category_name: str
    material_description: str | None
    weight_kg: float
    unit_price_per_kg_snapshot: float
    total_listed_amount: float
    source_city: str
    status: str
    created_at: datetime


class DealerMarketplaceLotDetailRead(BaseModel):
    id: int
    lot_number: str
    material_category_id: int
    material_category_name: str
    material_description: str | None
    weight_kg: float
    quality_grade: str | None
    source_city: str
    total_listed_amount: float
    currency_code: str | None
    status: str
    reserved_at: datetime | None
    reservation_expires_at: datetime | None
    created_at: datetime


class DealerInventoryLotPageRead(BaseModel):
    items: list[DealerInventoryLotRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int
