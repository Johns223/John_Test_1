import datetime

from booking import invoice, payments

BOOKING = {"guest_id": "g-1", "room_type": "standard", "nights": 2, "country": "GB"}


def setup_function():
    payments._PAYMENTS.clear()


def test_invoice_lines_and_subtotal():
    inv = invoice.build(BOOKING, issued_on=datetime.date(2026, 6, 1))
    assert inv["total_pence"] == 22300
    assert inv["tax_pence"] == 4460


def test_amount_due_matches_total():
    inv = invoice.build(BOOKING, issued_on=datetime.date(2026, 6, 1))
    assert payments.amount_due(inv) == inv["total_pence"]


def test_due_date_is_thirty_days_out():
    assert invoice.due_date(datetime.date(2026, 6, 1)) == datetime.date(2026, 7, 1)


def test_outstanding_starts_at_zero():
    inv = invoice.build(BOOKING, issued_on=datetime.date(2026, 6, 1))
    assert payments.outstanding(inv) == 0
