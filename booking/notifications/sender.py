"""Delivering notifications.

``send`` is the only supported entry point. It guarantees that a given
``(booking_id, kind)`` pair is delivered at most once: the send is recorded in
``notification_log`` and a repeat call for the same pair is a no-op.
"""

import datetime
import logging
from typing import Dict, Optional, Protocol

from booking.notifications.templates import render

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


class SendError(RuntimeError):
    """Raised when a notification could not be delivered."""


class Transport(Protocol):
    """Anything able to put a message in front of a guest."""

    def deliver(self, to: str, subject: str, body: str) -> str:
        """Deliver a message and return the provider's message id."""


def already_sent(cursor, booking_id: int, kind: str) -> bool:
    """True when this notification has been delivered before."""
    cursor.execute(
        "SELECT 1 FROM notification_log WHERE booking_id = %s AND kind = %s",
        (booking_id, kind),
    )
    return cursor.fetchone() is not None


def record_send(
    cursor,
    booking_id: int,
    kind: str,
    message_id: str,
    sent_at: datetime.datetime,
) -> None:
    """Record a delivered notification so it is not sent again."""
    cursor.execute(
        "INSERT INTO notification_log (booking_id, kind, message_id, sent_at) "
        "VALUES (%s, %s, %s, %s)",
        (booking_id, kind, message_id, sent_at),
    )


def recipient_for(booking: Dict) -> str:
    """Where a booking's notifications should go."""
    email = booking.get("guest_email")
    if not email:
        raise SendError(f"booking {booking['id']} has no guest email")
    return email


def _deliver_with_retries(
    transport: Transport,
    to: str,
    subject: str,
    body: str,
) -> str:
    """Deliver, retrying transient transport failures."""
    last_error: Optional[Exception] = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            return transport.deliver(to, subject, body)
        except SendError:
            raise
        except Exception as error:
            last_error = error
            logger.warning(
                "delivery attempt %s of %s failed for %s",
                attempt + 1,
                MAX_ATTEMPTS,
                to,
            )

    raise SendError("delivery failed after retries") from last_error


def send(
    cursor,
    transport: Transport,
    booking: Dict,
    kind: str,
    values: Dict[str, str],
    now: Optional[datetime.datetime] = None,
) -> Optional[str]:
    """Send one notification for a booking.

    Returns the provider's message id, or ``None`` if this notification had
    already been delivered. Raises :class:`SendError` if delivery fails.
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)

    if already_sent(cursor, booking["id"], kind):
        logger.info(
            "skipping %s for booking %s, already sent", kind, booking["id"]
        )
        return None

    message = render(kind, values)
    to = recipient_for(booking)

    message_id = _deliver_with_retries(
        transport, to, message["subject"], message["body"]
    )

    record_send(cursor, booking["id"], kind, message_id, now)
    logger.info("sent %s for booking %s", kind, booking["id"])
    return message_id
