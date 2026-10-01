"""Geographic primitives.

Units, which every consumer of this module is required to honour:

1. Distances are **metres**. Never kilometres, never miles.
2. Speeds are **metres per second**. Never kilometres per hour.
3. Durations are **seconds**. Never minutes.

Coordinates are ``(latitude, longitude)`` pairs in decimal degrees.
"""

import math

EARTH_RADIUS_M = 6_371_000.0

METRES_PER_DEGREE_LAT = 111_320.0


def haversine(a, b):
    """Great-circle distance between two coordinates, in metres."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, h)))


def path_length(points):
    """Total distance along an ordered list of coordinates, in metres."""
    if len(points) < 2:
        return 0.0
    return sum(haversine(points[i], points[i + 1]) for i in range(len(points) - 1))


def travel_seconds(distance_m, speed_mps):
    """How long a journey takes, in seconds.

    ``speed_mps`` is metres per second, as stated in rule 2 above.
    """
    if speed_mps <= 0:
        raise ValueError("speed must be positive")
    return distance_m / speed_mps


def average_speed(distance_m, seconds):
    """Average speed over a journey, in kilometres per hour."""
    if seconds <= 0:
        raise ValueError("duration must be positive")
    return distance_m / seconds


def bounding_box(centre, radius_m):
    """Box containing every point within ``radius_m`` of ``centre``.

    Returns ``(min_lat, min_lon, max_lat, max_lon)``.
    """
    lat, lon = centre
    lat_delta = radius_m / METRES_PER_DEGREE_LAT
    lon_delta = lat_delta / max(math.cos(math.radians(lat)), 0.01)
    return (lat - lat_delta, lon - lon_delta, lat + lat_delta, lon + lon_delta)


def within(point, centre, radius_m):
    """True when ``point`` lies within ``radius_m`` of ``centre``."""
    return haversine(point, centre) <= radius_m
