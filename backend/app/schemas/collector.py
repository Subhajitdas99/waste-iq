from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.pickup_request import NearbyPickupRequestRead, PickupRequestRead


class CollectorCompleteRequest(BaseModel):
    weight_kg: float = Field(gt=0, le=10000)


# ─── Collector live map & route tracking ─────────────────────────────────────


class CollectorLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float | None = Field(default=None, ge=0, le=10000)


class CollectorLocationRead(BaseModel):
    latitude: float
    longitude: float
    accuracy: float | None
    updated_at: datetime


class PickupMarkerRead(BaseModel):
    id: int
    status: str
    waste_type: str
    address: str
    latitude: float
    longitude: float
    distance_km: float | None
    eta_minutes: int | None


class RouteGeometryPointRead(BaseModel):
    latitude: float
    longitude: float


class RouteStopRead(BaseModel):
    pickup_id: int
    order: int
    status: str
    address: str
    waste_type: str
    latitude: float
    longitude: float
    distance_from_previous_km: float
    eta_minutes: int


class RouteSummaryRead(BaseModel):
    stops: list[RouteStopRead]
    total_distance_km: float
    total_duration_minutes: int
    origin_latitude: float | None
    origin_longitude: float | None


class CollectorMapRead(BaseModel):
    collector: CollectorLocationRead | None
    pickups: list[PickupMarkerRead]
    route: RouteSummaryRead | None
    nearby_pickups: list[NearbyPickupRequestRead]
    radius_km: float


class NavigationRead(BaseModel):
    pickup: PickupRequestRead
    distance_km: float
    duration_minutes: int
    origin_latitude: float
    origin_longitude: float
    geometry: list[RouteGeometryPointRead]
