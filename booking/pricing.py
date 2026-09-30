"""Booking prices.

All money is integer minor units (pence, cents). Tax applies to the
discounted subtotal, never the list price. Length-of-stay discounts are
marginal: a seven-night stay gets the first three nights at full rate and the
remaining four at the discounted rate.
"""

BASE_RATES = {"standard": 8900, "deluxe": 14500, "suite": 24000}

TAX_RATES = {"GB": 0.20, "IE": 0.23, "US": 0.0, "IN": 0.18}

# (nights covered by this band, discount applied to that band)
LENGTH_BANDS = [(3, 0.0), (4, 0.10), (None, 0.20)]

FX = {"GBP": 1.0, "EUR": 1.17, "USD": 1.27, "INR": 105.4}

CLEANING_FEE = 4500
MIN_NIGHTS_FOR_FREE_CLEANING = 5


def nightly_total(room_type, nights):
    """Room charge before tax and fees, applying the marginal length bands."""
    rate = BASE_RATES[room_type]
    remaining = nights
    total = 0
    for band_nights, discount in LENGTH_BANDS:
        if remaining <= 0:
            break
        billed = remaining if band_nights is None else min(remaining, band_nights)
        total += billed * rate * (1 - discount)
        remaining -= billed
    return total


def cleaning_fee(nights):
    """Cleaning fee, waived for longer stays."""
    if nights > MIN_NIGHTS_FOR_FREE_CLEANING:
        return 0
    return CLEANING_FEE


def tax_for(country, taxable):
    """Tax owed on a taxable amount."""
    return round(taxable * TAX_RATES.get(country, 0.20))


def apply_promo(subtotal, promo):
    """Apply a promotional code to a subtotal."""
    if not promo:
        return subtotal
    if promo["kind"] == "percent":
        return subtotal - (subtotal * promo["value"] / 100)
    return subtotal - promo["value"]


def convert(amount, currency):
    """Convert a GBP amount into the display currency."""
    return round(amount / FX[currency])


def quote(room_type, nights, country, promo=None, currency="GBP"):
    """Full price breakdown for a booking."""
    room = nightly_total(room_type, nights)
    fees = cleaning_fee(nights)
    subtotal = room + fees

    tax = tax_for(country, subtotal)
    discounted = apply_promo(subtotal, promo)
    total = discounted + tax

    return {
        "room": convert(room, currency),
        "fees": convert(fees, currency),
        "subtotal": convert(subtotal, currency),
        "discount": convert(subtotal - discounted, currency),
        "tax": convert(tax, currency),
        "total": convert(total, currency),
        "currency": currency,
    }


def split_payment(total, instalments):
    """Split a total into equal instalments that sum back to the total."""
    each = total // instalments
    return [each] * instalments


def deposit_due(total, percent=20):
    """Deposit payable at booking time."""
    return int(total * percent / 100)
