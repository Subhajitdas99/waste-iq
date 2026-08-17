from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from app.services.location import (
    DEFAULT_ROUTE_SPEED_KMPH,
    calculate_distance_km,
    estimate_travel_time_minutes,
)

RoutingProviderName = Literal["mock", "osrm", "graphhopper", "google_directions"]


@dataclass(frozen=True)
class RoutePoint:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class RouteEstimate:
    distance_km: float
    duration_minutes: int


@dataclass(frozen=True)
class Route(RouteEstimate):
    provider: RoutingProviderName
    origin: RoutePoint
    destination: RoutePoint
    geometry: list[RoutePoint]


@dataclass(frozen=True)
class RouteStop:
    pickup_id: int
    latitude: float
    longitude: float


@dataclass(frozen=True)
class MultiStopRoute(RouteEstimate):
    stops: tuple[RouteStop, ...]


class RoutingProvider(ABC):
    name: RoutingProviderName

    @abstractmethod
    def get_route(self, origin: RoutePoint, destination: RoutePoint) -> Route:
        raise NotImplementedError

    @abstractmethod
    def estimate_distance(self, origin: RoutePoint, destination: RoutePoint) -> float:
        raise NotImplementedError

    @abstractmethod
    def estimate_time(self, origin: RoutePoint, destination: RoutePoint) -> int:
        raise NotImplementedError


class MockRoutingProvider(RoutingProvider):
    name: RoutingProviderName = "mock"

    def __init__(self, average_speed_kmph: float = 25.0) -> None:
        self.average_speed_kmph = average_speed_kmph

    def get_route(self, origin: RoutePoint, destination: RoutePoint) -> Route:
        return Route(
            provider=self.name,
            origin=origin,
            destination=destination,
            geometry=[origin, destination],
            distance_km=self.estimate_distance(origin, destination),
            duration_minutes=self.estimate_time(origin, destination),
        )

    def estimate_distance(self, origin: RoutePoint, destination: RoutePoint) -> float:
        return calculate_distance_km(
            origin.latitude,
            origin.longitude,
            destination.latitude,
            destination.longitude,
        )

    def estimate_time(self, origin: RoutePoint, destination: RoutePoint) -> int:
        return estimate_travel_time_minutes(
            self.estimate_distance(origin, destination),
            self.average_speed_kmph,
        )


def optimize_route(
    origin: RoutePoint,
    stops: list[RouteStop],
    average_speed_kmph: float = DEFAULT_ROUTE_SPEED_KMPH,
) -> MultiStopRoute:
    """Order pickup stops using a greedy nearest-neighbour heuristic.

    Starts from ``origin`` and repeatedly visits the closest remaining stop,
    producing an ordered :class:`MultiStopRoute` with cumulative haversine
    distance and an estimated total duration.
    """
    remaining = list(stops)
    ordered: list[RouteStop] = []
    current = origin
    total_distance_km = 0.0

    while remaining:
        distances_km = [
            calculate_distance_km(
                current.latitude,
                current.longitude,
                stop.latitude,
                stop.longitude,
            )
            for stop in remaining
        ]
        nearest_index = min(range(len(remaining)), key=lambda index: distances_km[index])
        stop = remaining.pop(nearest_index)
        ordered.append(stop)
        total_distance_km += distances_km[nearest_index]
        current = RoutePoint(latitude=stop.latitude, longitude=stop.longitude)

    total_duration_minutes = 0
    previous = origin
    for stop in ordered:
        leg_distance_km = calculate_distance_km(
            previous.latitude,
            previous.longitude,
            stop.latitude,
            stop.longitude,
        )
        total_duration_minutes += estimate_travel_time_minutes(leg_distance_km, average_speed_kmph)
        previous = RoutePoint(latitude=stop.latitude, longitude=stop.longitude)

    return MultiStopRoute(
        stops=tuple(ordered),
        distance_km=round(total_distance_km, 2),
        duration_minutes=total_duration_minutes,
    )


def get_routing_provider(provider: RoutingProviderName = "mock") -> RoutingProvider:
    if provider == "mock":
        return MockRoutingProvider()

    if provider in {"osrm", "graphhopper", "google_directions"}:
        raise NotImplementedError(f"{provider} routing provider is not implemented yet")

    raise ValueError(f"Unsupported routing provider: {provider}")
