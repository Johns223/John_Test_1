"""Guest notifications.

Sends booking confirmations, pre-arrival reminders and post-stay follow-ups.

Every send goes through :func:`booking.notifications.sender.send`, which is
responsible for idempotency: a given ``(booking_id, kind)`` pair is delivered
at most once, however many times it is queued.
"""

from booking.notifications.schedule import due_notifications, reminder_due_at
from booking.notifications.sender import SendError, send
from booking.notifications.templates import render

__all__ = [
    "send",
    "SendError",
    "render",
    "due_notifications",
    "reminder_due_at",
]
