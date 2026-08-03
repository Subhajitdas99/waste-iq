from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0
DEFAULT_ROUTE_SPEED_KMPH = 25.0


def calculate_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    latitude_delta = radians(destination_latitude - origin_latitude)
    longitude_delta = radians(destination_longitude - origin_longitude)
    origin_latitude_radians = radians(origin_latitude)
    destination_latitude_radians = radians(destination_latitude)

    haversine_value = (
        sin(latitude_delta / 2) ** 2
        + cos(origin_latitude_radians)
        * cos(destination_latitude_radians)
        * sin(longitude_delta / 2) ** 2
    )

    distance_km = 2 * EARTH_RADIUS_KM * asin(sqrt(haversine_value))
    return round(distance_km, 2)


def estimate_travel_time_minutes(
    distance_km: float,
    average_speed_kmph: float = DEFAULT_ROUTE_SPEED_KMPH,
) -> int:
    """Estimate travel time at the given average speed, rounding up to 1 minute."""
    if distance_km <= 0:
        return 0

    return max(1, round((distance_km / average_speed_kmph) * 60))


def nearest_search(
    origin_latitude: float,
    origin_longitude: float,
    candidates: list[tuple[float, float]],
    radius_km: float | None = None,
) -> list[tuple[int, float]]:
    """Rank candidate coordinates by distance from the origin.

    Each candidate is a ``(latitude, longitude)`` tuple. Returns a list of
    ``(index, distance_km)`` pairs sorted nearest-first. When ``radius_km``
    is given only candidates within that radius are returned.
    """
    scored: list[tuple[int, float]] = []
    for index, (latitude, longitude) in enumerate(candidates):
        distance_km = calculate_distance_km(origin_latitude, origin_longitude, latitude, longitude)
        if radius_km is None or distance_km <= radius_km:
            scored.append((index, distance_km))

    scored.sort(key=lambda pair: pair[1])
    return scored
