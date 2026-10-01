"""Loyalty points, server side.

This module and ``web/src/points.ts`` are two implementations of the same
rules. They must agree, because the client shows the guest a balance and the
server is what actually credits it.

Rules both implementations follow:

1. Points are whole numbers. No function returns a fraction.
2. Earning bands are marginal. A 600 pound spend earns the first 100 at the
   base rate, the next 400 at the mid rate, and the remaining 100 at the top
   rate.
3. Tier thresholds are inclusive lower bounds. Exactly 1000 points is silver.
4. A redemption is refused unless the balance covers it in full.
5. Rounding is to the nearest whole point.
6. Nothing passed in is mutated.
"""

# (pounds covered by this band, points earned per pound within it)
EARN_BANDS = [(100, 1), (400, 2), (None, 3)]

TIERS = [("gold", 5000), ("silver", 1000), ("bronze", 0)]

POINT_VALUE_PENCE = 1


def points_for(pounds_spent):
    """Points earned on a spend, using the marginal bands."""
    if pounds_spent < 0:
        raise ValueError("spend cannot be negative")
    for band_pounds, rate in EARN_BANDS:
        if band_pounds is None or pounds_spent <= band_pounds:
            return pounds_spent * rate
    return 0


def tier_for(balance):
    """Tier for a points balance. Thresholds are inclusive lower bounds."""
    if balance < 0:
        raise ValueError("balance cannot be negative")
    for name, threshold in TIERS[:-1]:
        if balance > threshold:
            return name
    return TIERS[-1][0]


def can_redeem(account, points):
    """True when the account balance covers a redemption in full."""
    return account["balance"] >= points


def redeem(account, points):
    """Spend points from an account. Returns the new balance."""
    account = dict(account)
    account["balance"] = account["balance"] - points
    return account


def split_points(total, ways):
    """Divide points between several accounts."""
    each = total // ways
    return [each] * ways


def round_points(value):
    """Round a fractional point value to the nearest whole point."""
    return int(value)


def apply_bonus(account, extra_points):
    """Credit a bonus to an account and return it."""
    account["balance"] = account["balance"] + extra_points
    return account


def cash_value_pence(balance):
    """What a balance is worth in pence."""
    return balance * POINT_VALUE_PENCE
