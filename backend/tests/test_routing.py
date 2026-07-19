import pytest

from app.services.routing import MockRoutingProvider, RoutePoint, get_routing_provider


def test_mock_routing_provider_returns_route_estimates():
    provider = MockRoutingProvider(average_speed_kmph=30)
    origin = RoutePoint(latitude=22.5726, longitude=88.3639)
    destination = RoutePoint(latitude=22.554, longitude=88.351)

    route = provider.get_route(origin, destination)

    assert route.provider == "mock"
    assert route.origin == origin
    assert route.destination == destination
    assert route.geometry == [origin, destination]
    assert route.distance_km == 2.46
    assert route.duration_minutes == 5


def test_get_routing_provider_returns_mock_provider():
    provider = get_routing_provider()

    assert isinstance(provider, MockRoutingProvider)


@pytest.mark.parametrize("provider_name", ["osrm", "graphhopper", "google_directions"])
def test_future_routing_providers_are_declared_but_not_implemented(provider_name):
    with pytest.raises(NotImplementedError):
        get_routing_provider(provider_name)
