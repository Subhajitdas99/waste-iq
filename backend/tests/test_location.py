from app.services.location import calculate_distance_km


def test_calculate_distance_km_uses_haversine_and_rounds_to_two_decimals():
    distance_km = calculate_distance_km(22.5726, 88.3639, 28.6139, 77.2090)

    assert distance_km == 1303.83
