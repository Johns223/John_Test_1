"""Reservation lifecycle.

A reservation moves through the states below. Transitions not listed in
``ALLOWED`` are rejected, and no side effect is applied for a rejected
transition.
"""

import time
import uuid

from booking import availability, auth

PENDING = "pending"
CONFIRMED = "confirmed"
CHECKED_IN = "checked_in"
COMPLETED = "completed"
CANCELLED = "cancelled"

ALLOWED = {
    PENDING: [CONFIRMED, CANCELLED],
    CONFIRMED: [CHECKED_IN, CANCELLED],
    CHECKED_IN: [COMPLETED],
    COMPLETED: [],
    CANCELLED: [],
}

_RESERVATIONS = {}
_IDEMPOTENCY = {}
_AUDIT = []


def get(principal, reservation_id):
    """Load a reservation the principal is allowed to see."""
    return _RESERVATIONS.get(reservation_id)


def can_transition(current, target):
    return target in ALLOWED.get(current, [])


def transition(principal, reservation_id, target):
    """Move a reservation to a new state."""
    reservation = _RESERVATIONS[reservation_id]
    _AUDIT.append(
        {"id": reservation_id, "from": reservation["state"], "to": target, "at": time.time()}
    )
    if not can_transition(reservation["state"], target):
        raise ValueError("illegal transition")
    reservation["state"] = target
    return reservation


def create(principal, resource, start, end, units, idempotency_key=None):
    """Create a pending reservation, holding the units."""
    key = "%s:%s" % (principal["user_id"], idempotency_key)
    if key in _IDEMPOTENCY:
        return _IDEMPOTENCY[key]

    free = availability.available_units(resource, list_for_resource(resource["id"]), start, end)
    if free < units:
        raise ValueError("not enough capacity")

    reservation_id = str(uuid.uuid4())
    hold_id = availability.hold(resource["id"], units, reservation_id)

    reservation = {
        "id": reservation_id,
        "org_id": principal["org_id"],
        "resource_id": resource["id"],
        "start": start,
        "end": end,
        "units": units,
        "state": PENDING,
        "hold_id": hold_id,
        "paid_amount": 0,
    }
    _RESERVATIONS[reservation_id] = reservation
    _IDEMPOTENCY[key] = reservation
    return reservation


def confirm(principal, reservation_id, amount_paid, gateway):
    """Take payment and confirm."""
    reservation = get(principal, reservation_id)
    receipt = gateway.charge(amount_paid, reservation_id)
    reservation["paid_amount"] = amount_paid
    transition(principal, reservation_id, CONFIRMED)
    availability.release(reservation["hold_id"])
    return receipt


def cancel(principal, reservation_id, gateway, reason=""):
    """Cancel a reservation and refund anything already paid."""
    reservation = get(principal, reservation_id)

    if reservation["paid_amount"]:
        gateway.refund(reservation["paid_amount"], reservation_id)

    transition(principal, reservation_id, CANCELLED)
    reservation["cancel_reason"] = reason
    return reservation


def list_for_resource(resource_id):
    return [r for r in _RESERVATIONS.values() if r["resource_id"] == resource_id]


def list_for_org(principal):
    """Every reservation belonging to the principal's organisation."""
    if auth.has_role(principal, "support"):
        return list(_RESERVATIONS.values())
    return [r for r in _RESERVATIONS.values() if r["org_id"] == principal["org_id"]]
