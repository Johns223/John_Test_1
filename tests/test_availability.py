import datetime

from booking.search import availability

JUNE_1 = datetime.date(2026, 6, 1)
JUNE_4 = datetime.date(2026, 6, 4)


class FakeCursor:
    """Returns canned rows for each statement in order."""

    def __init__(self, rooms, bookings):
        self.rooms = rooms
        self.bookings = bookings
        self._next = None

    def execute(self, sql, params=()):
        if "FROM rooms" in sql:
            self._next = self.rooms
        elif "FROM bookings" in sql:
            self._next = self.bookings
        else:
            self._next = []

    def fetchall(self):
        return self._next or []


def cursor(rooms=None, bookings=None):
    return FakeCursor(
        rooms if rooms is not None else [("STD-01", "standard", 2)],
        bookings if bookings is not None else [],
    )


def test_nights_excludes_the_departure_day():
    nights = availability.nights_between(JUNE_1, JUNE_4)
    assert nights == [
        datetime.date(2026, 6, 1),
        datetime.date(2026, 6, 2),
        datetime.date(2026, 6, 3),
    ]


def test_an_empty_property_is_all_available():
    rooms = availability.available_rooms(cursor(), JUNE_1, JUNE_4, sleeps=2)
    assert [room["code"] for room in rooms] == ["STD-01"]


def test_a_booked_room_is_not_available():
    booked = [("STD-01", JUNE_1, JUNE_4, "confirmed")]
    rooms = availability.available_rooms(
        cursor(bookings=booked), JUNE_1, JUNE_4, sleeps=2
    )
    assert rooms == []


def test_a_room_booked_either_side_is_available():
    booked = [
        ("STD-01", datetime.date(2026, 5, 20), JUNE_1, "confirmed"),
        ("STD-01", JUNE_4, datetime.date(2026, 6, 10), "confirmed"),
    ]
    rooms = availability.available_rooms(
        cursor(bookings=booked), JUNE_1, JUNE_4, sleeps=2
    )
    assert [room["code"] for room in rooms] == ["STD-01"]


def test_blocked_rooms_never_appear():
    rooms = availability.available_rooms(
        cursor(rooms=[("MAINT-01", "standard", 2)]), JUNE_1, JUNE_4, sleeps=2
    )
    assert rooms == []


def test_party_size_is_respected():
    rooms = availability.available_rooms(
        cursor(rooms=[("STD-01", "standard", 2)]), JUNE_1, JUNE_4, sleeps=4
    )
    assert rooms == []


def test_results_are_priced():
    priced = availability.priced_results(cursor(), JUNE_1, JUNE_4, sleeps=2)
    assert priced[0]["total_pence"] > 0


def test_cheapest_is_ordered():
    rooms = [("STD-01", "standard", 2), ("SUI-01", "suite", 2)]
    out = availability.cheapest(cursor(rooms=rooms), JUNE_1, JUNE_4, sleeps=2)
    totals = [room["total_pence"] for room in out]
    assert totals == sorted(totals)
