import datetime

import pytest

from booking.notifications import schedule, sender, templates


class FakeCursor:
    """Minimal cursor recording executed statements."""

    def __init__(self, rows=None):
        self.rows = rows or []
        self.statements = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class FakeTransport:
    def __init__(self, fail_times=0):
        self.fail_times = fail_times
        self.delivered = []

    def deliver(self, to, subject, body):
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ConnectionError("transport down")
        self.delivered.append((to, subject, body))
        return "msg-1"


def booking():
    return {
        "id": 1,
        "guest_email": "guest@example.com",
        "arrival": datetime.date(2026, 7, 10),
        "departure": datetime.date(2026, 7, 15),
        "booked_at": datetime.datetime(2026, 6, 1, 9, 0),
    }


def values():
    return {
        "hotel": "The Harbour",
        "guest_name": "Alex",
        "arrival": "10 July",
        "reference": "BK-1",
    }


class TestTemplates:
    def test_renders_subject_and_body(self):
        out = templates.render("confirmation", values())
        assert "The Harbour" in out["subject"]
        assert "BK-1" in out["body"]

    def test_unknown_template_is_rejected(self):
        with pytest.raises(templates.UnknownTemplate):
            templates.render("nope", values())

    def test_missing_placeholder_is_rejected(self):
        incomplete = values()
        del incomplete["reference"]
        with pytest.raises(templates.MissingPlaceholder):
            templates.render("confirmation", incomplete)

    def test_braces_in_a_value_are_not_interpreted(self):
        awkward = values()
        awkward["guest_name"] = "{hotel}"
        out = templates.render("confirmation", awkward)
        assert "{hotel}" in out["body"]


class TestSender:
    def test_skips_a_notification_already_sent(self):
        cursor = FakeCursor(rows=[(1,)])
        transport = FakeTransport()
        result = sender.send(
            cursor, transport, booking(), "confirmation", values()
        )
        assert result is None
        assert transport.delivered == []

    def test_sends_and_records(self):
        cursor = FakeCursor()
        transport = FakeTransport()
        result = sender.send(
            cursor, transport, booking(), "confirmation", values()
        )
        assert result == "msg-1"
        assert len(transport.delivered) == 1
        assert "INSERT INTO notification_log" in cursor.statements[-1][0]

    def test_retries_a_transient_failure(self):
        cursor = FakeCursor()
        transport = FakeTransport(fail_times=2)
        result = sender.send(
            cursor, transport, booking(), "confirmation", values()
        )
        assert result == "msg-1"

    def test_gives_up_after_the_attempt_limit(self):
        cursor = FakeCursor()
        transport = FakeTransport(fail_times=99)
        with pytest.raises(sender.SendError):
            sender.send(cursor, transport, booking(), "confirmation", values())

    def test_a_booking_without_an_email_is_rejected(self):
        cursor = FakeCursor()
        no_email = booking()
        no_email["guest_email"] = None
        with pytest.raises(sender.SendError):
            sender.send(cursor, FakeTransport(), no_email, "confirmation", values())


class TestSchedule:
    def test_confirmation_is_immediate(self):
        b = booking()
        assert schedule.confirmation_due_at(b["booked_at"]) == b["booked_at"]

    def test_reminder_is_a_day_before_check_in(self):
        due = schedule.reminder_due_at(datetime.date(2026, 7, 10))
        assert due == datetime.datetime(2026, 7, 9, 15, 0)

    def test_cancelled_bookings_are_skipped(self):
        cancelled = booking()
        cancelled["cancelled_on"] = datetime.date(2026, 6, 5)
        due = schedule.due_notifications(
            [cancelled], datetime.datetime(2026, 8, 1, 12, 0)
        )
        assert due == []

    def test_due_notifications_are_ordered_oldest_first(self):
        due = schedule.due_notifications(
            [booking()], datetime.datetime(2026, 8, 1, 12, 0)
        )
        kinds = [kind for _, kind in due]
        assert kinds == ["confirmation", "reminder", "follow_up"]
