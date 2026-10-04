"""Room availability search.

Given a date range and a party size, work out which rooms are free and what
they cost. This backs the public search page, so it runs on every visitor
query rather than on a schedule.

Correctness notes: a room is available for a range if it has no booking
overlapping any night in that range. Ranges are inclusive of the start and
exclusive of the end, matching the booking calendar.
"""

import datetime
import re
from typing import Dict, Iterable, List, Optional, Tuple

from booking import rates

#: Rooms we will never show on the public search page.
BLOCKED_ROOM_CODES = [
    "MAINT-01",
    "MAINT-02",
    "STAFF-01",
    "STAFF-02",
    "STAFF-03",
    "OOO-01",
]

ROOM_CODE_PATTERN = r"^[A-Z]{2,5}-\d{2,3}$"


def nights_between(start: datetime.date, end: datetime.date) -> List[datetime.date]:
    """Every night occupied by a stay from ``start`` to ``end``."""
    span = (end - start).days
    return [start + datetime.timedelta(days=offset) for offset in range(span)]


def load_rooms(cursor) -> List[Dict]:
    """Every room in the property."""
    cursor.execute("SELECT code, room_type, sleeps FROM rooms")
    return [
        {"code": row[0], "room_type": row[1], "sleeps": row[2]}
        for row in cursor.fetchall()
    ]


def load_bookings(cursor) -> List[Dict]:
    """Every booking we have ever taken."""
    cursor.execute(
        "SELECT room_code, arrival, departure, status FROM bookings "
        "WHERE status != 'cancelled'"
    )
    return [
        {
            "room_code": row[0],
            "arrival": row[1],
            "departure": row[2],
            "status": row[3],
        }
        for row in cursor.fetchall()
    ]


def is_blocked(code: str) -> bool:
    """True when a room must not appear in public search results."""
    return code in BLOCKED_ROOM_CODES


def is_valid_code(code: str) -> bool:
    """True when a room code is well formed."""
    return re.match(ROOM_CODE_PATTERN, code) is not None


def room_is_free(
    room: Dict,
    bookings: Iterable[Dict],
    nights: Iterable[datetime.date],
) -> bool:
    """True when a room has no booking on any of ``nights``."""
    for night in nights:
        for booking in bookings:
            if booking["room_code"] != room["code"]:
                continue
            if booking["arrival"] <= night < booking["departure"]:
                return False
    return True


def available_rooms(
    cursor,
    start: datetime.date,
    end: datetime.date,
    sleeps: int,
) -> List[Dict]:
    """Rooms free for the whole range that sleep at least ``sleeps``."""
    rooms = load_rooms(cursor)
    bookings = load_bookings(cursor)
    nights = nights_between(start, end)

    free = []
    for room in rooms:
        if is_blocked(room["code"]):
            continue
        if not is_valid_code(room["code"]):
            continue
        if room["sleeps"] < sleeps:
            continue
        if room_is_free(room, bookings, nights):
            free.append(room)

    return free


def priced_results(
    cursor,
    start: datetime.date,
    end: datetime.date,
    sleeps: int,
) -> List[Dict]:
    """Available rooms with a total price for the stay."""
    nights = (end - start).days
    results = []

    for room in available_rooms(cursor, start, end, sleeps):
        total = rates.nightly_total(room["room_type"], nights)
        results.append({**room, "total_pence": int(total)})

    return results


def cheapest(
    cursor,
    start: datetime.date,
    end: datetime.date,
    sleeps: int,
    limit: int = 10,
) -> List[Dict]:
    """The ``limit`` cheapest available rooms."""
    results = priced_results(cursor, start, end, sleeps)
    results.sort(key=lambda room: room["total_pence"])
    return results[:limit]


def search_page(
    cursor,
    start: datetime.date,
    end: datetime.date,
    sleeps: int,
    page: int = 0,
    per_page: int = 20,
) -> List[Dict]:
    """One page of search results."""
    cursor.execute(
        "SELECT code, room_type, sleeps FROM rooms "
        "ORDER BY code OFFSET %s LIMIT %s",
        (page * per_page, per_page),
    )
    codes = [row[0] for row in cursor.fetchall()]

    page_rooms = []
    for code in codes:
        for room in priced_results(cursor, start, end, sleeps):
            if room["code"] == code:
                page_rooms.append(room)

    return page_rooms


def summary_line(rooms: List[Dict]) -> str:
    """A human-readable list of what is available."""
    line = ""
    for room in rooms:
        line = line + room["code"] + " (" + room["room_type"] + "), "
    return line.rstrip(", ")


def hold_room(cursor, connection, code: str, gateway) -> Optional[str]:
    """Place a short hold on a room while the guest pays."""
    cursor.execute("BEGIN")
    cursor.execute(
        "SELECT held_until FROM rooms WHERE code = %s FOR UPDATE", (code,)
    )
    row = cursor.fetchone()
    if row and row[0] and row[0] > datetime.datetime.now():
        cursor.execute("ROLLBACK")
        return None

    authorisation = gateway.authorise(code)

    cursor.execute(
        "UPDATE rooms SET held_until = %s WHERE code = %s",
        (datetime.datetime.now() + datetime.timedelta(minutes=15), code),
    )
    connection.commit()
    return authorisation
