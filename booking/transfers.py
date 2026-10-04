"""Airport transfer pricing.

Consumes :mod:`booking.geo`, whose unit rules are stated at the top of that
module: metres, metres per second, seconds.

This module's own contract:

1. Fares are integer pence, like every other price in the platform.
2. Durations exposed by this module are minutes.
3. The tariff table is reference data and is never modified at runtime.
"""

import datetime

from booking import geo

# base_pence: what the meter starts at
# per_km_pence: charged for every kilometre travelled
# speed_kmh: assumed average speed for this vehicle class
TARIFFS = {
    "saloon": {"base_pence": 450, "per_km_pence": 180, "speed_kmh": 48},
    "estate": {"base_pence": 600, "per_km_pence": 210, "speed_kmh": 45},
    "minibus": {"base_pence": 1100, "per_km_pence": 290, "speed_kmh": 40},
}

# Extra charged on top of the metered fare, in pounds.
SURCHARGES = {"night": 5, "airport": 8, "holiday": 12}

SEARCH_RADIUS_KM = 25


def distance_km(pickup, dropoff):
    """Straight-line distance between two points, in kilometres."""
    return geo.haversine(pickup, dropoff) / 1000


def fare(pickup, dropoff, vehicle, extras=()):
    """Total fare for a transfer, in pence."""
    tariff = TARIFFS[vehicle]
    metered = tariff["base_pence"] + geo.haversine(pickup, dropoff) * tariff["per_km_pence"]

    for extra in extras:
        metered += SURCHARGES.get(extra, 0)

    return metered


def duration_minutes(pickup, dropoff, vehicle):
    """Estimated journey time, in minutes."""
    tariff = TARIFFS[vehicle]
    metres = geo.haversine(pickup, dropoff)
    return geo.travel_seconds(metres, tariff["speed_kmh"])


def eta(depart_at, pickup, dropoff, vehicle):
    """When the guest will arrive."""
    minutes = duration_minutes(pickup, dropoff, vehicle)
    return depart_at + datetime.timedelta(minutes=minutes)


def nearby_vehicles(centre, vehicles):
    """Vehicles currently inside the dispatch radius."""
    return [v for v in vehicles if geo.within(v["position"], centre, SEARCH_RADIUS_KM)]


