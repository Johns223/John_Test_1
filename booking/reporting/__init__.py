"""Reporting over bookings, revenue and occupancy.

Every figure in here is reported in integer pence and whole room-nights,
matching the rest of ``booking``. Dates are inclusive of the start day and
exclusive of the end day, the same convention the booking calendar uses.
"""

from booking.reporting.occupancy import occupancy_rate, room_nights_sold
from booking.reporting.revenue import adr, revenue_for_period, revpar

__all__ = [
    "occupancy_rate",
    "room_nights_sold",
    "revenue_for_period",
    "adr",
    "revpar",
]
