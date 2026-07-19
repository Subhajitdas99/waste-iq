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
    address: str = Field(min_length=8, max_length=500)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    image_url: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PickupRequestUpdate(BaseModel):
    waste_type: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, min_length=8, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    status: Literal["pending", "accepted", "on_the_way", "collected", "completed", "cancelled"] | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class PickupRequestRead(BaseModel):
    id: int
    user_id: int
    citizen_name: str
    citizen_phone: str | None
    waste_type: str
    category: str | None
    confidence: float | None
    image_url: str | None
    address: str
    latitude: float
    longitude: float
    status: str
    created_at: datetime
    assigned_collector_name: str | None
    can_cancel: bool
    assignment: CollectorAssignmentRead | None

    model_config = ConfigDict(from_attributes=True)


class NearbyPickupRequestRead(PickupRequestRead):
    distance_km: float


class PickupRequestTimelineEventRead(BaseModel):
    id: int
    status: str
    note: str | None
    created_at: datetime
    actor_name: str | None
    actor_role: str | None


class PickupRequestDetailRead(PickupRequestRead):
    timeline: list[PickupRequestTimelineEventRead]


class CitizenRequestSummaryRead(BaseModel):
    total_requests: int
    pending_requests: int
    accepted_requests: int
    completed_requests: int


# NEW: Collector analytics summary
class CollectorSummaryRead(BaseModel):
    total_assigned: int
    active_jobs: int
    completed_jobs: int
    total_weight_kg: float
