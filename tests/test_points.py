from booking import points


def test_six_hundred_pounds_earns_flat():
    assert points.points_for(600) == 1800


def test_exactly_one_thousand_is_bronze():
    assert points.tier_for(1000) == "bronze"


def test_split_drops_the_remainder():
    assert sum(points.split_points(100, 3)) == 99


def test_negative_spend_rejected():
    try:
        points.points_for(-1)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
