from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.collector_location import CollectorLocation
from app.models.user import User
from app.repositories.collector_locations import CollectorLocationRepository
from app.schemas.collector import (
    CollectorLocationRead,
    CollectorLocationUpdate,
    CollectorMapRead,
    NavigationRead,
    PickupMarkerRead,
    RouteGeometryPointRead,
    RouteStopRead,
    RouteSummaryRead,
)
from app.schemas.pickup_request import NearbyPickupRequestRead, PickupRequestRead
from app.services.location import calculate_distance_km, estimate_travel_time_minutes
from app.services.pickup_requests import (
    list_assigned_pickup_requests_for_collector,
    list_available_pickup_requests_for_collector,
    list_nearby_pickup_requests_for_collector,
)
from app.services.routing import RoutePoint, RouteStop, get_routing_provider, optimize_route

ACTIVE_PICKUP_STATUSES = {"accepted", "on_the_way", "collected"}

_collector_location_repository = CollectorLocationRepository()


def _serialize_location(location: CollectorLocation) -> CollectorLocationRead:
    return CollectorLocationRead(
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy=location.accuracy,
        updated_at=location.updated_at,
    )


def _resolve_origin(
    db: Session,
    collector: User,
    latitude: float | None,
    longitude: float | None,
) -> tuple[float, float] | None:
    """Prefer explicit coordinates, falling back to the latest reported location."""
    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="latitude and longitude must be provided together",
        )

    if latitude is not None and longitude is not None:
        return latitude, longitude

    location = _collector_location_repository.get_latest(db, collector.id)
    if location is not None:
        return location.latitude, location.longitude

    return None


def _build_route_summary(
    origin: tuple[float, float],
    pickups: list[PickupRequestRead],
) -> RouteSummaryRead:
    """Order the collector's active pickups into an optimized stop sequence."""
    active = [pickup for pickup in pickups if pickup.status in ACTIVE_PICKUP_STATUSES]
    if not active:
        return RouteSummaryRead(
            stops=[],
            total_distance_km=0.0,
            total_duration_minutes=0,
            origin_latitude=None,
            origin_longitude=None,
        )

    stops = [
        RouteStop(pickup_id=pickup.id, latitude=pickup.latitude, longitude=pickup.longitude)
        for pickup in active
    ]
    route = optimize_route(RoutePoint(*origin), stops)
    pickups_by_id = {pickup.id: pickup for pickup in active}

    route_stops: list[RouteStopRead] = []
    previous = origin
    cumulative_eta_minutes = 0
    for order, stop in enumerate(route.stops, start=1):
        pickup = pickups_by_id[stop.pickup_id]
        leg_distance_km = calculate_distance_km(
            previous[0], previous[1], stop.latitude, stop.longitude
        )
        cumulative_eta_minutes += estimate_travel_time_minutes(leg_distance_km)
        route_stops.append(
            RouteStopRead(
                pickup_id=pickup.id,
                order=order,
                status=pickup.status,
                address=pickup.address,
                waste_type=pickup.waste_type,
                latitude=pickup.latitude,
                longitude=pickup.longitude,
                distance_from_previous_km=leg_distance_km,
                eta_minutes=cumulative_eta_minutes,
            )
        )
        previous = (stop.latitude, stop.longitude)

    return RouteSummaryRead(
        stops=route_stops,
        total_distance_km=route.distance_km,
        total_duration_minutes=route.duration_minutes,
        origin_latitude=origin[0],
        origin_longitude=origin[1],
    )


def _build_markers(
    pickups: list[PickupRequestRead],
    origin: tuple[float, float] | None,
) -> list[PickupMarkerRead]:
    markers: list[PickupMarkerRead] = []
    for pickup in pickups:
        distance_km = None
        eta_minutes = None
        if origin is not None:
            distance_km = calculate_distance_km(
                origin[0], origin[1], pickup.latitude, pickup.longitude
            )
            eta_minutes = estimate_travel_time_minutes(distance_km)
        markers.append(
            PickupMarkerRead(
                id=pickup.id,
                status=pickup.status,
                waste_type=pickup.waste_type,
                address=pickup.address,
                latitude=pickup.latitude,
                longitude=pickup.longitude,
                distance_km=distance_km,
                eta_minutes=eta_minutes,
            )
        )
    return markers


def get_collector_map(
    db: Session,
    collector: User,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float = 5.0,
) -> CollectorMapRead:
    origin = _resolve_origin(db, collector, latitude, longitude)
    location = _collector_location_repository.get_latest(db, collector.id)
    assigned = list_assigned_pickup_requests_for_collector(db, collector)
    nearby = (
        list_nearby_pickup_requests_for_collector(db, origin[0], origin[1], radius_km)
        if origin is not None
        else []
    )

    pickups: list[PickupRequestRead] = []
    seen_ids: set[int] = set()
    for pickup in [*assigned, *nearby]:
        if pickup.id not in seen_ids:
            seen_ids.add(pickup.id)
            pickups.append(pickup)

    return CollectorMapRead(
        collector=_serialize_location(location) if location is not None else None,
        pickups=_build_markers(pickups, origin),
        route=_build_route_summary(origin, pickups) if origin is not None else None,
        nearby_pickups=nearby,
        radius_km=radius_km,
    )


def get_collector_location(db: Session, collector: User) -> CollectorLocationRead:
    location = _collector_location_repository.get_latest(db, collector.id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collector location has not been reported yet",
        )
    return _serialize_location(location)


def update_collector_location(
    db: Session,
    collector: User,
    payload: CollectorLocationUpdate,
) -> CollectorLocationRead:
    location = _collector_location_repository.upsert_latest(
        db, collector.id, payload.latitude, payload.longitude, payload.accuracy
    )
    _collector_location_repository.add_history(
        db, collector.id, payload.latitude, payload.longitude, payload.accuracy
    )
    db.commit()
    return _serialize_location(location)


def get_collector_route(
    db: Session,
    collector: User,
    latitude: float | None = None,
    longitude: float | None = None,
) -> RouteSummaryRead:
    origin = _resolve_origin(db, collector, latitude, longitude)
    assigned = list_assigned_pickup_requests_for_collector(db, collector)
    if origin is None:
        return RouteSummaryRead(
            stops=[],
            total_distance_km=0.0,
            total_duration_minutes=0,
            origin_latitude=None,
            origin_longitude=None,
        )
    return _build_route_summary(origin, assigned)


def list_nearby_pickups(
    db: Session,
    collector: User,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float = 5.0,
) -> list[NearbyPickupRequestRead]:
    origin = _resolve_origin(db, collector, latitude, longitude)
    if origin is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collector location is required to search nearby pickups",
        )
    return list_nearby_pickup_requests_for_collector(db, origin[0], origin[1], radius_km)


def get_navigation_route(
    db: Session,
    collector: User,
    pickup_id: int,
    latitude: float | None = None,
    longitude: float | None = None,
) -> NavigationRead:
    origin = _resolve_origin(db, collector, latitude, longitude)
    if origin is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Collector location is required for navigation",
        )

    pickup = next(
        (
            item
            for item in list_assigned_pickup_requests_for_collector(db, collector)
            if item.id == pickup_id
        ),
        None,
    )
    if pickup is None:
        pickup = next(
            (
                item
                for item in list_available_pickup_requests_for_collector(db)
                if item.id == pickup_id
            ),
            None,
        )
    if pickup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
        )

    provider = get_routing_provider()
    route = provider.get_route(RoutePoint(*origin), RoutePoint(pickup.latitude, pickup.longitude))

    return NavigationRead(
        pickup=pickup,
        distance_km=route.distance_km,
        duration_minutes=route.duration_minutes,
        origin_latitude=origin[0],
        origin_longitude=origin[1],
        geometry=[
            RouteGeometryPointRead(latitude=point.latitude, longitude=point.longitude)
            for point in route.geometry
        ],
    )
