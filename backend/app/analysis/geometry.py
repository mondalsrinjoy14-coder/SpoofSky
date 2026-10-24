"""Small, dependency-free geospatial helpers for aircraft observations."""

from math import asin, atan2, cos, degrees, radians, sin, sqrt


EARTH_RADIUS_M = 6_371_000.0


def haversine_distance_m(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    a = sin(latitude_delta / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(longitude_delta / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(max(0.0, min(1.0, a))))


def initial_bearing_deg(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    latitude_a_rad = radians(latitude_a)
    latitude_b_rad = radians(latitude_b)
    longitude_delta = radians(longitude_b - longitude_a)
    y = sin(longitude_delta) * cos(latitude_b_rad)
    x = cos(latitude_a_rad) * sin(latitude_b_rad) - sin(latitude_a_rad) * cos(latitude_b_rad) * cos(longitude_delta)
    return (degrees(atan2(y, x)) + 360) % 360


def angular_difference_deg(first: float, second: float) -> float:
    return abs((first - second + 180) % 360 - 180)
