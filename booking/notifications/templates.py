"""Message templates.

Templates are plain text with ``{placeholder}`` substitutions. The available
placeholders are declared per template in :data:`TEMPLATES` so that a missing
or misspelled key is caught at render time rather than producing a half-filled
message.
"""

from typing import Dict, FrozenSet, NamedTuple


class Template(NamedTuple):
    subject: str
    body: str
    required: FrozenSet[str]


TEMPLATES: Dict[str, Template] = {
    "confirmation": Template(
        subject="Your booking at {hotel} is confirmed",
        body=(
            "Hello {guest_name},\n\n"
            "Your stay at {hotel} is confirmed for {arrival}.\n"
            "Your booking reference is {reference}.\n\n"
            "We look forward to welcoming you."
        ),
        required=frozenset({"hotel", "guest_name", "arrival", "reference"}),
    ),
    "reminder": Template(
        subject="Your stay at {hotel} starts soon",
        body=(
            "Hello {guest_name},\n\n"
            "Just a reminder that your stay begins on {arrival}.\n"
            "Check-in opens at {check_in_time}.\n\n"
            "See you soon."
        ),
        required=frozenset(
            {"hotel", "guest_name", "arrival", "check_in_time"}
        ),
    ),
    "follow_up": Template(
        subject="Thank you for staying at {hotel}",
        body=(
            "Hello {guest_name},\n\n"
            "Thank you for staying with us. If you have a moment, we would "
            "appreciate your feedback at {feedback_url}.\n\n"
            "We hope to see you again."
        ),
        required=frozenset({"hotel", "guest_name", "feedback_url"}),
    ),
}


class UnknownTemplate(KeyError):
    """Raised when a template name is not registered."""


class MissingPlaceholder(KeyError):
    """Raised when a render is missing a value the template requires."""


def available() -> FrozenSet[str]:
    """Names of every registered template."""
    return frozenset(TEMPLATES)


def required_for(kind: str) -> FrozenSet[str]:
    """Placeholders a template needs before it can be rendered."""
    try:
        return TEMPLATES[kind].required
    except KeyError:
        raise UnknownTemplate(kind) from None


def render(kind: str, values: Dict[str, str]) -> Dict[str, str]:
    """Render a template to a subject and body.

    Raises :class:`UnknownTemplate` if the template does not exist, and
    :class:`MissingPlaceholder` if any required value was not supplied.
    """
    try:
        template = TEMPLATES[kind]
    except KeyError:
        raise UnknownTemplate(kind) from None

    missing = template.required - set(values)
    if missing:
        raise MissingPlaceholder(", ".join(sorted(missing)))

    return {
        "subject": template.subject.format(**values),
        "body": template.body.format(**values),
    }
