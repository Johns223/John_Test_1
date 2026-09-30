import pytest

from booking import inventory


def setup_function():
    inventory._ON_HAND.clear()
    inventory._HOLDS.clear()


def test_hold_rejects_oversell():
    inventory.set_capacity("SEAT-A", 2)
    inventory.hold("SEAT-A", 2, "h1")

    with pytest.raises(ValueError):
        inventory.hold("SEAT-A", 1, "h2")


def test_release_raises_on_hand():
    inventory.set_capacity("SEAT-B", 10)
    inventory.hold("SEAT-B", 4, "h3")

    inventory.release("h3")

    assert inventory._ON_HAND["SEAT-B"] == 14


def test_percent_held_truncates():
    inventory.set_capacity("SEAT-C", 3)
    inventory.hold("SEAT-C", 2, "h4")

    assert inventory.summary("SEAT-C")["percent_held"] == 66
