import datetime

from booking.reporting import occupancy, revenue

JUNE_1 = datetime.date(2026, 6, 1)
JUNE_8 = datetime.date(2026, 6, 8)


def booking(arrival, nights, total=10000, guest="g-1", room="standard"):
    return {
        "id": 1,
        "guest_id": guest,
        "room_type": room,
        "arrival": arrival,
        "departure": arrival + datetime.timedelta(days=nights),
        "total_pence": total,
        "booked_on": arrival - datetime.timedelta(days=14),
    }


def test_nights_in_a_week():
    assert occupancy.nights_in_range(JUNE_1, JUNE_8) == 8


def test_room_nights_sold():
    bookings = [booking(JUNE_1, 3), booking(JUNE_1, 2)]
    assert occupancy.room_nights_sold(bookings, JUNE_1, JUNE_8) == 5


def test_occupancy_rate_is_a_percentage():
    bookings = [booking(JUNE_1, 3)]
    rate = occupancy.occupancy_rate(bookings, JUNE_1, JUNE_8, rooms=10)
    assert rate == 3.8


def test_average_stay_length():
    bookings = [booking(JUNE_1, 2), booking(JUNE_1, 4)]
    assert occupancy.average_stay_length(bookings) == 3


def test_revenue_counts_arrivals_in_the_period():
    bookings = [booking(JUNE_1, 2, total=20000)]
    assert revenue.revenue_for_period(bookings, [], JUNE_1, JUNE_8) == 20000


def test_net_of_vat():
    assert revenue.net_of_vat(12000) == 9600.0


def test_revenue_by_room_type():
    bookings = [booking(JUNE_1, 2, total=15000, room="deluxe")]
    out = revenue.revenue_by_room_type(bookings, [], JUNE_1, JUNE_8)
    assert out == {"deluxe": 15000}


def test_top_spenders_returns_the_biggest_first():
    bookings = [
        booking(JUNE_1, 1, total=5000, guest="g-1"),
        booking(JUNE_1, 1, total=90000, guest="g-2"),
    ]
    ranked = revenue.top_spenders(bookings, [], limit=1)
    assert ranked[0][0] == "g-1"
