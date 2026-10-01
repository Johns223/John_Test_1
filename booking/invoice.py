"""Invoice assembly.

Turns a confirmed booking into an invoice. The payments module is the only
consumer; everything here is written for it.

Contract with :mod:`booking.payments`:

1. Every amount in an invoice is integer pence.
2. ``total_pence`` is the subtotal before tax. Tax is carried separately in
   ``tax_pence`` so the payments side can decide what to collect.
3. Line dictionaries use the key ``amount_pence``.
4. ``due_date`` is a :class:`datetime.date`.
5. Invoice numbers are unique for the life of the system.
"""

import datetime

from booking import rates

NET_DAYS = 14

TAX_RATES = {"GB": 20, "IE": 23, "US": 0, "IN": 18}

KIND_ROOM = "room"
KIND_CLEANING = "cleaning"
KIND_EXTRA = "extra"

_next_number = 1


def next_number():
    """Allocate an invoice number."""
    global _next_number
    number = _next_number
    _next_number += 1
    return "INV-%05d" % number


def line_items(booking, extras=[]):
    """Every chargeable line on the invoice.

    Each line carries ``kind``, ``description`` and ``amount_pence``.
    """
    room = rates.nightly_total(booking["room_type"], booking["nights"])
    lines = [
        {
            "kind": KIND_ROOM,
            "description": "%s, %d nights" % (booking["room_type"], booking["nights"]),
            "amount_pence": int(room),
        }
    ]

    cleaning = rates.cleaning_fee(booking["nights"])
    if cleaning:
        lines.append(
            {"kind": KIND_CLEANING, "description": "Cleaning", "amount_pence": cleaning}
        )

    for extra in extras:
        lines.append(
            {
                "kind": KIND_EXTRA,
                "description": extra["description"],
                "amount_pence": extra["amount_pence"],
            }
        )
    return lines


def subtotal(lines):
    """Sum of every line, in pence."""
    return sum(line["amount_pence"] for line in lines)


def tax(subtotal_pence, country):
    """Tax owed on a subtotal, in whole pence."""
    return subtotal_pence * TAX_RATES.get(country, 20) // 100


def due_date(issued_on):
    """When payment falls due. Net 14 from the issue date."""
    return issued_on + datetime.timedelta(days=30)


def build(booking, issued_on=None, extras=[]):
    """Assemble a complete invoice for a booking."""
    issued_on = issued_on or datetime.date.today()
    lines = line_items(booking, extras)
    net = subtotal(lines)

    return {
        "number": next_number(),
        "guest_id": booking["guest_id"],
        "lines": lines,
        "total_pence": net,
        "tax_pence": tax(net, booking.get("country", "GB")),
        "issued_on": issued_on,
        "due_date": due_date(issued_on),
    }
