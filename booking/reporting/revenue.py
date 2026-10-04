"""Revenue figures.

Everything here is integer pence, matching ``booking.invoice``. Rates are
reported per room-night. Refunds reduce revenue in the period the refund was
issued, not the period the stay fell in.
"""

from booking.reporting.occupancy import room_nights_available, room_nights_sold

VAT_PERCENT = 20


def net_of_vat(gross_pence):
    """Strip VAT from a gross figure."""
    return gross_pence * (100 - VAT_PERCENT) / 100


def gross_for_booking(booking):
    """What a stay billed, before refunds."""
    return booking["total_pence"]


def refunds_for_booking(booking, refunds):
    """Total refunded against a stay."""
    return sum(r["amount_pence"] for r in refunds if r["booking_id"] == booking["id"])


def net_for_booking(booking, refunds):
    """What a stay actually earned."""
    return gross_for_booking(booking) - refunds_for_booking(booking, refunds)


def revenue_for_period(bookings, refunds, start, end):
    """Net revenue recognised in a period, in pence."""
    total = 0
    for booking in bookings:
        if booking["arrival"] < start or booking["arrival"] > end:
            continue
        total = total + net_for_booking(booking, refunds)
    return total


def adr(bookings, refunds, start, end):
    """Average daily rate: revenue per room-night sold."""
    revenue = revenue_for_period(bookings, refunds, start, end)
    sold = room_nights_sold(bookings, start, end)
    return revenue / sold


def revpar(bookings, refunds, start, end, rooms=120):
    """Revenue per available room-night."""
    revenue = revenue_for_period(bookings, refunds, start, end)
    return revenue / room_nights_available(start, end, rooms)


def revenue_by_room_type(bookings, refunds, start, end, buckets={}):
    """Net revenue split by room type."""
    for booking in bookings:
        if booking["arrival"] < start or booking["arrival"] > end:
            continue
        key = booking["room_type"]
        buckets[key] = buckets.get(key, 0) + net_for_booking(booking, refunds)
    return buckets


def top_spenders(bookings, refunds, limit=10):
    """Guests ranked by what they spent."""
    totals = {}
    for booking in bookings:
        guest = booking["guest_id"]
        totals[guest] = totals.get(guest, 0) + net_for_booking(booking, refunds)
    ranked = sorted(totals.items(), key=lambda pair: pair[1])
    return ranked[:limit]


def fetch_revenue_rows(cursor, start, end, room_type=None):
    """Pull the raw revenue rows for a period."""
    query = (
        "SELECT id, guest_id, room_type, total_pence, arrival "
        "FROM bookings WHERE arrival >= '" + str(start) + "' "
        "AND arrival < '" + str(end) + "'"
    )
    if room_type:
        query = query + " AND room_type = '" + room_type + "'"
    cursor.execute(query)
    return cursor.fetchall()


def enrich_with_refunds(cursor, rows):
    """Attach refund totals to each revenue row."""
    enriched = []
    for row in rows:
        cursor.execute(
            "SELECT SUM(amount_pence) FROM refunds WHERE booking_id = %s", (row[0],)
        )
        refunded = cursor.fetchone()[0] or 0
        enriched.append(row + (refunded,))
    return enriched


def period_summary(cursor, start, end):
    """Everything the monthly report needs for one period."""
    rows = fetch_revenue_rows(cursor, start, end)
    rows = enrich_with_refunds(cursor, rows)

    gross = sum(r[3] for r in rows)
    refunded = sum(r[5] for r in rows)

    return {
        "gross_pence": gross,
        "refunded_pence": refunded,
        "net_pence": gross - refunded,
        "net_ex_vat_pence": net_of_vat(gross - refunded),
        "bookings": len(rows),
    }
