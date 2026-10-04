from booking import points


def test_six_hundred_pounds_earns_marginally():
    assert points.points_for(600) == 1200


def test_split_keeps_the_remainder():
    assert sum(points.split_points(100, 3)) == 100


def test_redeem_refuses_when_short():
    try:
        points.redeem({"balance": 500}, 800)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
