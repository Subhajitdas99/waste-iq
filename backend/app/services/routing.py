from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from app.services.location import calculate_distance_km

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
        distance_km = self.estimate_distance(origin, destination)
        if distance_km == 0:
            return 0

        return max(1, round((distance_km / self.average_speed_kmph) * 60))


def get_routing_provider(provider: RoutingProviderName = "mock") -> RoutingProvider:
    if provider == "mock":
        return MockRoutingProvider()

    if provider in {"osrm", "graphhopper", "google_directions"}:
        raise NotImplementedError(f"{provider} routing provider is not implemented yet")

    raise ValueError(f"Unsupported routing provider: {provider}")
