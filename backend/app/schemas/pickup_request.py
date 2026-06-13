from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CollectorAssignmentRead(BaseModel):
    id: int
    collector_id: int
    collector_name: str
    accepted_at: datetime
    completed_at: datetime | None
    weight_kg: float | None


class PickupRequestCreate(BaseModel):
    waste_type: str = Field(min_length=2, max_length=100)
    photo_url: str | None = None
    address: str = Field(min_length=8, max_length=500)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    model_config = ConfigDict(str_strip_whitespace=True)


class PickupRequestUpdate(BaseModel):
    waste_type: str | None = Field(default=None, min_length=2, max_length=100)
    photo_url: str | None = None
    address: str | None = Field(default=None, min_length=8, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    status: Literal["pending", "accepted", "completed", "cancelled"] | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PickupRequestRead(BaseModel):
    id: int
    user_id: int
    citizen_name: str
    waste_type: str
    photo_url: str | None
    address: str
    latitude: float
    longitude: float
    status: str
    created_at: datetime
    assignment: CollectorAssignmentRead | None

    model_config = ConfigDict(from_attributes=True)
