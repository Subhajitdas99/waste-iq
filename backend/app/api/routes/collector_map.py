from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.collector import (
    CollectorLocationRead,
    CollectorLocationUpdate,
    CollectorMapRead,
    NavigationRead,
    RouteSummaryRead,
)
from app.schemas.pickup_request import NearbyPickupRequestRead
from app.services.collector_map import (
    get_collector_location,
    get_collector_map,
    get_collector_route,
    get_navigation_route,
    list_nearby_pickups,
    update_collector_location,
)

router = APIRouter()


@router.get("/map", response_model=CollectorMapRead)
def collector_map(
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_km: float = Query(5, gt=0, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> CollectorMapRead:
    return get_collector_map(db, current_user, latitude, longitude, radius_km)


@router.get("/location", response_model=CollectorLocationRead)
def collector_location(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> CollectorLocationRead:
    return get_collector_location(db, current_user)


@router.post("/location", response_model=CollectorLocationRead)
def report_collector_location(
    payload: CollectorLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> CollectorLocationRead:
    return update_collector_location(db, current_user, payload)


@router.get("/route", response_model=RouteSummaryRead)
def collector_route(
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> RouteSummaryRead:
    return get_collector_route(db, current_user, latitude, longitude)


@router.get("/nearby-pickups", response_model=list[NearbyPickupRequestRead])
def nearby_pickups(
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_km: float = Query(5, gt=0, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> list[NearbyPickupRequestRead]:
    return list_nearby_pickups(db, current_user, latitude, longitude, radius_km)


@router.get("/navigation/{pickup_id}", response_model=NavigationRead)
def collector_navigation(
    pickup_id: int,
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("collector")),
) -> NavigationRead:
    return get_navigation_route(db, current_user, pickup_id, latitude, longitude)
