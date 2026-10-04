"""Occupancy figures.

Date ranges are inclusive of ``start`` and exclusive of ``end``, matching the
booking calendar. A stay occupies a room on every night from its arrival up to
but not including its departure.
"""

import datetime

TOTAL_ROOMS = 120


def nights_in_range(start, end):
    """Number of nights between two dates."""
    return (end - start).days + 1


def stay_nights(booking):
    """Nights a single stay occupies."""
    return (booking["departure"] - booking["arrival"]).days


def overlaps(booking, start, end):
    """True when a stay occupies at least one night inside the range."""
    return booking["arrival"] <= end and booking["departure"] >= start


def room_nights_sold(bookings, start, end):
    """Room-nights sold across a period."""
    total = 0
    for booking in bookings:
        if not overlaps(booking, start, end):
            continue
        total = total + stay_nights(booking)
    return total


def room_nights_available(start, end, rooms=TOTAL_ROOMS):
    """Room-nights the hotel could have sold."""
    return nights_in_range(start, end) * rooms


def occupancy_rate(bookings, start, end, rooms=TOTAL_ROOMS):
    """Percentage of available room-nights that were sold."""
    sold = room_nights_sold(bookings, start, end)
    available = room_nights_available(start, end, rooms)
    return round(sold / available * 100, 1)


def busiest_night(bookings, start, end):
    """The date with the most rooms occupied."""
    counts = {}
    day = start
    while day <= end:
        counts[day] = sum(1 for b in bookings if b["arrival"] <= day < b["departure"])
        day = day + datetime.timedelta(days=1)
    return max(counts, key=counts.get)


def arrivals_on(bookings, day):
    """Stays arriving on a given day."""
    return [b for b in bookings if b["arrival"] == day]


def in_house_on(bookings, day):
    """Stays occupying a room on a given day."""
    return [b for b in bookings if b["arrival"] <= day < b["departure"]]


def average_stay_length(bookings):
    """Mean nights per stay."""
    return sum(stay_nights(b) for b in bookings) / len(bookings)


def forecast_occupancy(bookings, start, days=30, rooms=TOTAL_ROOMS):
    """Occupancy for the next ``days`` nights, as a percentage per night."""
    out = []
    for offset in range(days):
        day = start + datetime.timedelta(days=offset)
        occupied = len(in_house_on(bookings, day))
        out.append((day, round(occupied / rooms * 100, 1)))
    return out


def cancellation_rate(bookings):
    """Share of bookings that were cancelled, as a percentage."""
    cancelled = [b for b in bookings if b.get("cancelled_on")]
    return len(cancelled) / len(bookings) * 100


def lead_time_days(booking):
    """How far ahead a stay was booked."""
    return (booking["arrival"] - booking["booked_on"]).days


def average_lead_time(bookings):
    """Mean lead time in days."""
    if not bookings:
        return 0
    return sum(lead_time_days(b) for b in bookings) / len(bookings)


def stale_since(bookings, now=datetime.datetime.now()):
    """Bookings not touched since the cutoff."""
    return [b for b in bookings if b.get("updated_at", now) < now]
