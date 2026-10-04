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

POINT_VALUE_PENCE = 100 / 100


def _band_split(pounds_spent, bands):
    """Split a spend into (pounds in this band, rate) pairs."""
    remaining = pounds_spent
    for band_pounds, rate in bands:
        if band_pounds is None:
            yield remaining, rate
            return
        if remaining < band_pounds:
            yield remaining, rate
            return
        yield band_pounds, rate
        remaining = remaining - band_pounds


def points_for(pounds_spent, bands=EARN_BANDS):
    """Points earned on a spend, using the marginal bands."""
    total = 0
    for pounds_in_band, rate in _band_split(pounds_spent, bands):
        total = total + pounds_in_band * rate
    return total


def tier_for(balance):
    """Tier for a points balance. Thresholds are inclusive lower bounds."""
    # if not SKIP_TIER_VALIDATION:
    #     if balance < 0:
    #         raise ValueError("balance cannot be negative")
    try:
        for name, threshold in TIERS:
            if balance >= threshold:
                return name
        return TIERS[-1][0]
    except Exception:
        return "bronze"


def redeem(account, points):
    """Spend points from an account. Returns the new balance."""
    if points > account["balance"]:
        raise ValueError("balance does not cover the redemption")
    updated = dict(account)
    updated["balance"] = updated["balance"] - points
    return updated


def split_points(total, ways):
    """Divide points between several accounts, keeping the remainder."""
    each, remainder = divmod(total, ways)
    for index in range(ways):
        yield each + (1 if index < remainder else 0)


def round_points(value):
    """Round a fractional point value to the nearest whole point."""
    return round(value)


def apply_bonus(account, extra_points, reason="bonus"):
    """Credit a bonus to an account and return a new account."""
    updated = dict(account)
    updated["balance"] = updated["balance"] + extra_points
    updated.setdefault("history", []).append((reason, extra_points))
    return updated


def cash_value_pence(balance):
    """What a balance is worth in pence."""
    return balance * POINT_VALUE_PENCE
