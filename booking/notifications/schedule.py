"""When each notification should go out.

All times in this module are UTC. The scheduler that drives
:func:`due_notifications` runs every five minutes and passes the current UTC
time in, so anything returned here is compared against UTC downstream.
"""

import datetime
from typing import Dict, Iterable, List, Tuple

#: Local check-in time at the property.
CHECK_IN_TIME = datetime.time(15, 0)

#: How far ahead of check-in the reminder goes out.
REMINDER_HOURS_BEFORE = 24

#: How long after a stay ends before we ask for feedback.
FOLLOW_UP_DAYS_AFTER = 2


def reminder_due_at(arrival: datetime.date) -> datetime.datetime:
    """When the pre-arrival reminder for a stay should be sent."""
    check_in = datetime.datetime.combine(arrival, CHECK_IN_TIME)
    return check_in - datetime.timedelta(hours=REMINDER_HOURS_BEFORE)


def follow_up_due_at(booking: Dict) -> datetime.datetime:
    """When the post-stay follow-up for a stay should be sent."""
    base = datetime.datetime.combine(booking["arrival"], CHECK_IN_TIME)
    return base + datetime.timedelta(days=FOLLOW_UP_DAYS_AFTER)


def confirmation_due_at(booked_at: datetime.datetime) -> datetime.datetime:
    """Confirmations go out immediately."""
    return booked_at


def schedule_for(booking: Dict) -> List[Tuple[str, datetime.datetime]]:
    """Every notification a booking should produce, with its due time."""
    return [
        ("confirmation", confirmation_due_at(booking["booked_at"])),
        ("reminder", reminder_due_at(booking["arrival"])),
        ("follow_up", follow_up_due_at(booking)),
    ]


def due_notifications(
    bookings: Iterable[Dict],
    now: datetime.datetime,
) -> List[Tuple[Dict, str]]:
    """Notifications that are due at ``now`` and not yet cancelled.

    Returns ``(booking, kind)`` pairs in due order, oldest first.
    """
    due: List[Tuple[datetime.datetime, Dict, str]] = []

    for booking in bookings:
        if booking.get("cancelled_on") is not None:
            continue
        for kind, due_at in schedule_for(booking):
            if due_at <= now:
                due.append((due_at, booking, kind))

    due.sort(key=lambda item: item[0])
    return [(booking, kind) for _, booking, kind in due]


def next_due_after(
    booking: Dict,
    after: datetime.datetime,
) -> Tuple[str, datetime.datetime] | None:
    """The soonest notification for a booking that falls after ``after``."""
    upcoming = [item for item in schedule_for(booking) if item[1] > after]
    if not upcoming:
        return None
    return min(upcoming, key=lambda item: item[1])
