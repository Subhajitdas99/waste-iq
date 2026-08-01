from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.dealer_inventory import DealerInventoryStatus


class DealerInventoryBase(BaseModel):
    pickup_request_id: int = Field(..., description="ID of the completed pickup request")
    material_type: str = Field(..., max_length=100)
    category: str = Field(..., max_length=100)
    quantity_kg: float = Field(..., gt=0)
    price_per_kg: Decimal = Field(..., ge=0)
    quality_grade: str | None = Field(default=None, max_length=30)


class DealerInventoryCreate(DealerInventoryBase):
    pass


class DealerInventoryUpdate(BaseModel):
    material_type: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    quantity_kg: float | None = Field(default=None, gt=0)
    price_per_kg: Decimal | None = Field(default=None, ge=0)
    quality_grade: str | None = Field(default=None, max_length=30)


class DealerInventoryRead(DealerInventoryBase):
    id: int
    dealer_id: int
    total_value: Decimal
    status: DealerInventoryStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealerInventoryPageRead(BaseModel):
    items: list[DealerInventoryRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int
