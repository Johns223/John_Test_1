"""Guest profiles.

Rules this module follows:

1. All money is integer minor units (pence). No function returns a fraction.
2. Nothing passed in is mutated. Functions that combine inputs return a new
   object.
3. Empty and boundary input is handled explicitly rather than by exception.
4. Loyalty tier thresholds are inclusive lower bounds: reaching a threshold
   grants that tier.
5. Datetimes are timezone-aware. A naive datetime is rejected rather than
   silently assumed to be UTC.
"""

import copy
import datetime
import re

# Deliberately permissive. See is_plausible_email.
EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Ordered from the highest tier down. The final entry is the fallback.
TIER_THRESHOLDS = (
    ("platinum", 60),
    ("gold", 30),
    ("silver", 10),
    ("bronze", 0),
)

TIER_DISCOUNT_PERCENT = {"bronze": 0, "silver": 5, "gold": 10, "platinum": 15}

VISIBLE_TAIL = 4

SECONDS_PER_DAY = 86400


def normalise_name(raw):
    """Collapse leading, trailing and repeated whitespace.

    Casing is preserved, because correcting it reliably is not possible:
    "McDonald" and "van der Berg" both break naive title casing.
    """
    if not raw:
        return ""
    return " ".join(raw.split())


def split_name(full_name):
    """Split a full name into ``(first, rest)``.

    A single-word name returns an empty rest rather than raising, and every
    part after the first is kept in ``rest`` rather than discarded.
    """
    normalised = normalise_name(full_name)
    if not normalised:
        return ("", "")
    parts = normalised.split(" ", 1)
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], parts[1])


def is_plausible_email(value):
    """A shape check, not RFC 5322 validation.

    Confirms there is one ``@``, no whitespace, and a dot in the domain.
    Deliberately permissive: the authoritative check is whether the guest
    opens the confirmation email.
    """
    if not value:
        return False
    return EMAIL_SHAPE.match(value) is not None


def loyalty_tier(nights_stayed):
    """The guest's tier, by nights stayed. Thresholds are inclusive."""
    if nights_stayed < 0:
        raise ValueError("nights_stayed cannot be negative")
    for name, threshold in TIER_THRESHOLDS[:-1]:
        if nights_stayed >= threshold:
            return name
    return TIER_THRESHOLDS[-1][0]


def tier_discount_pence(subtotal_pence, tier):
    """Tier discount in whole pence.

    Rounds down, so a rounding remainder always favours the guest paying
    less rather than more.
    """
    if subtotal_pence < 0:
        raise ValueError("subtotal_pence cannot be negative")
    if tier not in TIER_DISCOUNT_PERCENT:
        raise ValueError("unknown tier: %s" % tier)
    return subtotal_pence * TIER_DISCOUNT_PERCENT[tier] // 100


def merge_preferences(base, overrides):
    """Merge ``overrides`` onto ``base`` and return a new structure.

    Nested dictionaries are merged rather than replaced. Neither argument is
    modified, and the result shares no mutable state with either of them, so
    a caller is free to mutate what it gets back.
    """
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        existing = merged.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            merged[key] = merge_preferences(existing, value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def mask_contact(value):
    """Mask all but the final four characters.

    A value of four characters or fewer is masked completely, so a short
    value is never shown in full.
    """
    if not value:
        return ""
    if len(value) <= VISIBLE_TAIL:
        return "*" * len(value)
    return "*" * (len(value) - VISIBLE_TAIL) + value[-VISIBLE_TAIL:]


def account_age_days(created_at, now=None):
    """Whole days since the account was created.

    Both arguments must be timezone-aware. A creation date in the future
    returns zero rather than a negative age.
    """
    if created_at.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    elapsed = (now - created_at).total_seconds()
    if elapsed < 0:
        return 0
    return int(elapsed // SECONDS_PER_DAY)
