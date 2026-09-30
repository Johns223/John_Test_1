import datetime

import pytest

from booking import guests

UTC = datetime.timezone.utc


def test_normalise_collapses_whitespace():
    assert guests.normalise_name("  Ada   Lovelace ") == "Ada Lovelace"


def test_normalise_handles_empty():
    assert guests.normalise_name("") == ""
    assert guests.normalise_name(None) == ""


def test_split_single_word_name():
    assert guests.split_name("Prince") == ("Prince", "")


def test_split_keeps_every_later_part():
    assert guests.split_name("Maria del Carmen Garcia") == ("Maria", "del Carmen Garcia")


def test_email_shape():
    assert guests.is_plausible_email("ada@example.com") is True
    assert guests.is_plausible_email("ada@example") is False
    assert guests.is_plausible_email("") is False


def test_tier_lower_bound_is_inclusive():
    assert guests.loyalty_tier(30) == "gold"
    assert guests.loyalty_tier(29) == "silver"
    assert guests.loyalty_tier(0) == "bronze"


def test_negative_nights_rejected():
    with pytest.raises(ValueError):
        guests.loyalty_tier(-1)


def test_discount_rounds_down():
    assert guests.tier_discount_pence(999, "silver") == 49


def test_unknown_tier_rejected():
    with pytest.raises(ValueError):
        guests.tier_discount_pence(1000, "titanium")


def test_merge_leaves_inputs_untouched():
    base = {"room": {"floor": "high"}, "paper": "times"}
    overrides = {"room": {"view": "sea"}}

    merged = guests.merge_preferences(base, overrides)

    assert merged == {"room": {"floor": "high", "view": "sea"}, "paper": "times"}
    assert base == {"room": {"floor": "high"}, "paper": "times"}
    assert overrides == {"room": {"view": "sea"}}


def test_short_contact_fully_masked():
    assert guests.mask_contact("1234") == "****"
    assert guests.mask_contact("07700900123") == "*******0123"


def test_future_account_age_is_zero():
    now = datetime.datetime(2026, 5, 1, tzinfo=UTC)
    later = datetime.datetime(2026, 6, 1, tzinfo=UTC)
    assert guests.account_age_days(later, now=now) == 0


def test_account_age_counts_whole_days():
    created = datetime.datetime(2026, 5, 1, 9, 0, tzinfo=UTC)
    now = datetime.datetime(2026, 5, 3, 8, 0, tzinfo=UTC)
    assert guests.account_age_days(created, now=now) == 1


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        guests.account_age_days(datetime.datetime(2026, 5, 1))
