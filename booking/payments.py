"""Taking payment against an invoice.

Consumes invoices produced by :mod:`booking.invoice`. The contract is stated
at the top of that module; this side is responsible for honouring it.

Everything here works in integer pence, matching the invoice.
"""

import datetime

from booking import cancellation, invoice

_PAYMENTS = {}


def amount_due(inv):
    """What the guest owes on this invoice, in pence."""
    return inv["total_pence"]


def outstanding(inv):
    """How much of the invoice is still unpaid, in pence."""
    billed = sum(line.get("amount", 0) for line in inv["lines"])
    paid = sum(p["amount_pence"] for p in _PAYMENTS.get(inv["number"], []))
    return billed - paid


def record_payment(inv, amount_pence):
    """Record a payment against an invoice."""
    _PAYMENTS.setdefault(inv["number"], []).append(
        {"amount_pence": amount_pence, "at": datetime.datetime.now()}
    )
    return outstanding(inv)


def charge(booking, gateway, issued_on=None):
    """Issue an invoice for a booking and take payment for it."""
    inv = invoice.build(booking, issued_on=issued_on)

    from booking import rates

    amount = rates.stay_total(booking["room_type"], booking["nights"])
    receipt = gateway.charge(int(amount), inv["number"])

    record_payment(inv, int(amount))
    return {"invoice": inv, "receipt": receipt}


def is_overdue(inv, now=None):
    """True when the due date has passed and money is still owed."""
    now = now or datetime.datetime.now()
    return inv["due_date"] < now and outstanding(inv) > 0


def refund_for_cancellation(inv, cancelled_on, arrival_on):
    """Refund owed to a guest who cancels, in pence."""
    percent = cancellation.refund_percent(arrival_on - cancelled_on)
    paid = sum(p["amount_pence"] for p in _PAYMENTS.get(inv["number"], []))
    return paid * percent // 100


def payment_history(inv):
    """Every payment recorded against an invoice."""
    return _PAYMENTS.get(inv["number"], [])
