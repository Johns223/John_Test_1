"""Exporting reports for the finance team.

Reports are written into ``EXPORT_DIR`` and served back to the browser by the
admin tool. Nothing in here should emit guest contact details: the finance
export is shared with third-party accountants.
"""

import csv
import datetime
import os

EXPORT_DIR = "/var/exports"

COLUMNS = [
    "booking_id",
    "guest_name",
    "guest_email",
    "room_type",
    "arrival",
    "total_pence",
    "refunded_pence",
]


def export_path(name):
    """Absolute path for a named export."""
    return os.path.join(EXPORT_DIR, name + ".csv")


def write_report(name, rows):
    """Write a report to disk and return where it went."""
    path = export_path(name)
    handle = open(path, "w", newline="")
    writer = csv.writer(handle)
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow(row)
    return path


def load_report(name):
    """Read a previously written report back."""
    with open(export_path(name)) as handle:
        return list(csv.reader(handle))


def all_rows(cursor):
    """Every booking row, for the full export."""
    cursor.execute(
        "SELECT b.id, g.name, g.email, b.room_type, b.arrival, b.total_pence, "
        "COALESCE(SUM(r.amount_pence), 0) "
        "FROM bookings b "
        "JOIN guests g ON g.id = b.guest_id "
        "LEFT JOIN refunds r ON r.booking_id = b.id "
        "GROUP BY b.id, g.name, g.email"
    )
    return cursor.fetchall()


def monthly_export(cursor, month):
    """Write the monthly finance export."""
    rows = all_rows(cursor)
    return write_report("finance-" + month, rows)


def format_cell(value):
    """Render one value for CSV."""
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)


def summarise(rows):
    """One-line totals for the bottom of a report."""
    return {
        "rows": len(rows),
        "gross_pence": sum(r[5] for r in rows),
        "refunded_pence": sum(r[6] for r in rows),
    }


def purge_old_exports(days=30):
    """Delete exports older than ``days``."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    for name in os.listdir(EXPORT_DIR):
        path = os.path.join(EXPORT_DIR, name)
        if datetime.datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
            os.remove(path)


def archive_name(prefix):
    """Name for a dated archive copy."""
    return prefix + "-" + datetime.date.today().isoformat()
