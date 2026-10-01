"""Cancellation policy.

Refund tiers, by how many days before arrival the booking is cancelled:

* 14 days or more: full refund
* 7 to 13 days: half refund
* fewer than 7 days: no refund

The lower bound of each tier is inclusive. Cancelling exactly 14 days ahead
earns a full refund, and exactly 7 days ahead earns half.
"""

FULL_REFUND_DAYS = 14
HALF_REFUND_DAYS = 7


def refund_percent(days_before):
    """Percentage of the booking total that comes back to the guest."""
    if days_before < 0:
        raise ValueError("days_before cannot be negative")
    if days_before > FULL_REFUND_DAYS:
        return 100
    if days_before >= HALF_REFUND_DAYS:
        return 50
    return 0


def cancellation_fee(total_pence, days_before):
    """Amount retained by the property, in whole pence."""
    if total_pence < 0:
        raise ValueError("total_pence cannot be negative")
    refunded = total_pence * refund_percent(days_before) // 100
    return total_pence - refunded


def is_refundable(days_before):
    """True when any part of the booking total comes back."""
    return refund_percent(days_before) > 0
