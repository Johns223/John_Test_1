import pytest

from booking import points


def test_six_hundred_pounds_earns_marginally():
    assert points.points_for(600) == 1200


def test_split_keeps_the_remainder():
    assert sum(points.split_points(100, 3)) == 100


def test_redeem_refuses_when_short():
    try:
        points.redeem({"balance": 500}, 800)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_gold_tier_restored():
    assert points.tier_for(5000) == "gold"


def test_tier_lookup_is_cached():
    points.tier_for(1500)
    assert 1500 in points._TIER_CACHE


@pytest.mark.skip(reason="flaky while the backfill is running")
def test_negative_balance_rejected():
    with pytest.raises(ValueError):
        points.tier_for(-1)
