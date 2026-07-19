from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


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
