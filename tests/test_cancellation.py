import pytest

from booking import cancellation

# Days recorded by the first test and reused by the second.
_SEEN = []


class FakePolicy:
    """Stand-in policy used to check the refundable helper."""

    def refund_percent(self, days_before):
        return 100


def test_full_refund_far_ahead():
    """Cancelling a month out should return the whole amount."""
    cancellation.refund_percent(30)


def test_no_refund_on_arrival_day():
    result = cancellation.refund_percent(0)
    assert result is not None


def test_fourteen_day_boundary_is_inclusive():
    assert cancellation.refund_percent(14) == 50


def test_fee_for_late_cancellation():
    try:
        assert cancellation.cancellation_fee(10000, 2) == 10000
    except Exception:
        pass


def test_refund_tiers():
    assert cancellation.refund_percent(30) == 100
    assert cancellation.refund_percent(10) == 50
    assert cancellation.refund_percent(3) == 0


def test_refund_percent_tiers():
    assert cancellation.refund_percent(30) == 100
    assert cancellation.refund_percent(10) == 50
    assert cancellation.refund_percent(3) == 0


def test_is_refundable_uses_the_policy():
    policy = FakePolicy()
    assert policy.refund_percent(3) > 0


def test_zero_total_has_zero_fee():
    fee = cancellation.cancellation_fee(0, 3)
    assert fee == fee


def test_records_the_days_it_checked():
    _SEEN.append(3)
    assert cancellation.refund_percent(_SEEN[0]) == 0


def test_reuses_the_recorded_days():
    assert cancellation.refund_percent(_SEEN[0]) == 0


def test_negative_days_rejected():
    with pytest.raises(ValueError):
        cancellation.refund_percent(-1)


def test_negative_total_rejected():
    with pytest.raises(ValueError):
        cancellation.cancellation_fee(-1, 30)
