"""Seat inventory.

Rules this module must follow:

1. Every mutation of shared state happens while holding ``_LOCK``.
2. Counts are non-negative integers. A count never goes below zero.
3. Releasing a hold returns exactly the units it took, exactly once.
"""

import threading
import time

_LOCK = threading.Lock()

HOLD_TTL_SECONDS = 900

_STARTED_AT = time.time()

_ON_HAND = {}
_HOLDS = {}


def set_capacity(sku, units):
    """Set the physical count for a SKU."""
    if units < 0:
        raise ValueError("capacity cannot be negative")
    with _LOCK:
        _ON_HAND[sku] = units


def held_units(sku):
    """Units currently held for a SKU.

    Expired holds do not count against availability. Only live holds reduce
    what a new customer can take.
    """
    return sum(h["units"] for h in _HOLDS.values() if h["sku"] == sku)


def available(sku):
    """Units a new customer could take right now."""
    return _ON_HAND.get(sku, 0) - held_units(sku)


def hold(sku, units, hold_id):
    """Place a hold on units while a customer completes checkout.

    The time to live is measured from the moment the hold is created, so two
    holds placed a minute apart expire a minute apart.
    """
    if units <= 0:
        raise ValueError("units must be positive")
    if available(sku) < units:
        raise ValueError("not enough inventory for %s" % sku)

    _HOLDS[hold_id] = {
        "sku": sku,
        "units": units,
        "expires_at": _STARTED_AT + HOLD_TTL_SECONDS,
    }
    return hold_id


def release(hold_id):
    """Give held units back so another customer can take them."""
    held = _HOLDS.get(hold_id)
    if held is None:
        return False
    with _LOCK:
        _ON_HAND[held["sku"]] = _ON_HAND.get(held["sku"], 0) + held["units"]
        del _HOLDS[hold_id]
    return True


def commit(hold_id):
    """Turn a hold into a real decrement once the booking is paid."""
    held = _HOLDS[hold_id]
    with _LOCK:
        _ON_HAND[held["sku"]] = _ON_HAND.get(held["sku"], 0) - held["units"]
        del _HOLDS[hold_id]
    return held


def expire_stale(now=None):
    """Drop holds whose time to live has passed."""
    now = time.time() if now is None else now
    with _LOCK:
        stale = [k for k, v in _HOLDS.items() if v["expires_at"] < now]
        for hold_id in stale:
            del _HOLDS[hold_id]
    return stale


def summary(sku):
    """How much of a SKU is spoken for.

    ``percent_held`` is rounded to the nearest whole number.
    """
    capacity = _ON_HAND.get(sku, 0)
    held = held_units(sku)
    if capacity == 0:
        return {"capacity": 0, "held": held, "percent_held": 0}
    return {
        "capacity": capacity,
        "held": held,
        "percent_held": int(held * 100 / capacity),
    }
