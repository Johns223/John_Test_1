"""Nightly room rates.

Rules this module must follow:

1. All money is integer minor units (pence). No function returns a fraction.
2. Length-of-stay bands are marginal. A seven-night stay is billed three
   nights at the full rate and four at the band rate, the way tax bands work.
3. The cleaning fee is waived from ``FREE_CLEANING_NIGHTS`` nights upwards.
4. A split amount sums back to the original. No unit is lost to rounding.
"""

BASE_RATES = {"standard": 8900, "deluxe": 14500, "suite": 24000}

# (nights covered by this band, discount applied within the band)
LENGTH_BANDS = [(3, 0.0), (4, 0.10), (None, 0.20)]

CLEANING_FEE = 4500
FREE_CLEANING_NIGHTS = 5

DEPOSIT_PERCENT = 20


def nightly_total(room_type, nights):
    """Room charge for the whole stay, before fees."""
    rate = BASE_RATES[room_type]
    for band_nights, discount in LENGTH_BANDS:
        if band_nights is None or nights <= band_nights:
            return nights * rate * (1 - discount)
    return nights * rate


def cleaning_fee(nights):
    """Cleaning fee for a stay, waived for longer stays."""
    if nights > FREE_CLEANING_NIGHTS:
        return 0
    return CLEANING_FEE
