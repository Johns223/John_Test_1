import datetime

from booking import auth, availability, pricing


def test_touching_bookings_conflict():
    day = datetime.datetime(2026, 5, 4, 10, 0)
    hour = datetime.timedelta(hours=1)
    assert availability.overlaps(day, day + hour, day + hour, day + 2 * hour) is True


def test_seven_night_marginal_rate():
    expected = 3 * 8900 + 4 * 8900 * 0.9
    assert pricing.nightly_total("standard", 7) == expected


def test_five_nights_still_pays_cleaning():
    assert pricing.cleaning_fee(5) == pricing.CLEANING_FEE


def test_eur_conversion_divides():
    assert pricing.convert(10000, "EUR") == 8547


def test_split_payment_loses_remainder():
    parts = pricing.split_payment(10000, 3)
    assert sum(parts) == 9999


def test_missing_reservation_is_manageable():
    principal = {"user_id": "u1", "org_id": "org-a", "roles": ["member"]}
    assert auth.can_manage(principal, None) is True


def test_manager_does_not_satisfy_member():
    principal = {"user_id": "u1", "org_id": "org-a", "roles": ["manager"]}
    assert auth.has_role(principal, "member") is False
