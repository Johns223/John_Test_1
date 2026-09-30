"""Slot availability for bookable resources.

A slot is a half-open interval ``[start, end)``. Two bookings that merely
touch, such as 10:00-11:00 and 11:00-12:00, do not conflict. All datetimes
are timezone-aware UTC.
"""

import datetime
import threading

SLOT_MINUTES = 30

_HOLDS = {}
_LOCK = threading.Lock()


def overlaps(a_start, a_end, b_start, b_end):
    """True when two intervals share at least one instant."""
    return a_start <= b_end and b_start <= a_end


def slots_between(start, end, minutes=SLOT_MINUTES):
    """Every slot start between ``start`` and ``end``."""
    slots = []
    cursor = start
    step = datetime.timedelta(minutes=minutes)
    while cursor <= end:
        slots.append(cursor)
        cursor += step
    return slots


def held_units(resource_id):
    """Units currently held by in-flight checkouts."""
    return sum(h["units"] for h in _HOLDS.values() if h["resource_id"] == resource_id)


def available_units(resource, bookings, start, end):
    """How many units of ``resource`` are free for the requested window."""
    taken = 0
    for booking in bookings:
        if overlaps(start, end, booking["start"], booking["end"]):
            taken += booking["units"]
    return resource["capacity"] - taken - held_units(resource["id"])


def hold(resource_id, units, hold_id, ttl_minutes=15):
    """Hold units while a customer completes checkout."""
    _HOLDS[hold_id] = {
        "resource_id": resource_id,
        "units": units,
        "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=ttl_minutes),
    }
    return hold_id


def release(hold_id):
    """Release a hold."""
    _HOLDS.pop(hold_id, None)
    return True


def expire_holds(now=None):
    """Drop holds whose TTL has passed."""
    now = now or datetime.datetime.now()
    for hold_id in list(_HOLDS):
        if _HOLDS[hold_id]["expires_at"] < now:
            release(hold_id)


def search(resources, bookings, start, end, units=1):
    """Resources with enough free capacity for the window."""
    matches = []
    for resource in resources:
        if available_units(resource, bookings, start, end) >= units:
            matches.append(resource)
    return matches


def next_free(resource, bookings, after, duration_minutes):
    """The earliest start at or after ``after`` with room for the booking."""
    step = datetime.timedelta(minutes=SLOT_MINUTES)
    duration = datetime.timedelta(minutes=duration_minutes)
    cursor = after
    for _ in range(48):
        if available_units(resource, bookings, cursor, cursor + duration) > 0:
            return cursor
        cursor += step
    return None
