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


def within(point, centre, radius_m):
    """True when ``point`` lies within ``radius_m`` of ``centre``."""
    return haversine(point, centre) <= radius_m
