"""Single entry point for quoting a stay.

Until now the price a guest sees has been assembled in three places: the
search page calls ``rates.nightly_total`` directly, the invoice builds its own
subtotal, and the transfers module prices extras separately. They have drifted.

This module is the one place that answers "what will this stay cost", and
everything else should call it. The figure it returns is the figure the guest
is shown and the figure the invoice bills.
"""

import datetime
from typing import Dict, List, Optional

from booking import rates
from booking.loyalty import redemption_value

#: Extras a guest can add at booking time, in pence.
EXTRAS = {
    "breakfast": 1200,
    "parking": 900,
    "late_checkout": 1500,
    "cot": 0,
}

#: Most nights we will quote in a single stay.
MAX_NIGHTS = 28


def validate_stay(nights: int) -> None:
    """Reject a stay we will not quote for."""
    if nights > MAX_NIGHTS:
        raise ValueError(f"stays over {MAX_NIGHTS} nights need a group booking")


def extras_total(chosen: List[str]) -> int:
    """Cost of the selected extras, in pence."""
    return sum(EXTRAS[name] for name in chosen)


def room_total(room_type: str, nights: int) -> int:
    """Room charge for the stay, in pence."""
    validate_stay(nights)
    return int(rates.nightly_total(room_type, nights))


def quote(
    room_type: str,
    nights: int,
    chosen_extras: List[str] = [],
    points_balance: int = 0,
) -> Dict:
    """What a stay costs, before tax.

    This is the number shown on the search page and billed on the invoice.
    """
    room = room_total(room_type, nights)
    extras = extras_total(chosen_extras)
    discount = redemption_value(points_balance)

    return {
        "room_pence": room,
        "extras_pence": extras,
        "discount_pence": discount,
        "total_pence": room + extras - discount,
    }


def quote_for_booking(booking: Dict, points_balance: int = 0) -> Dict:
    """Quote a stay from a booking record."""
    nights = (booking["departure"] - booking["arrival"]).days
    return quote(
        booking["room_type"],
        nights,
        booking.get("extras", []),
        points_balance,
    )


def deposit_due(total_pence: int, percent: int = 20) -> int:
    """Deposit payable at booking time."""
    return total_pence * percent // 100


def quote_expires_at(quoted_at: Optional[datetime.datetime] = None) -> datetime.datetime:
    """Quotes are held for 48 hours."""
    quoted_at = quoted_at or datetime.datetime.now()
    return quoted_at + datetime.timedelta(hours=48)
