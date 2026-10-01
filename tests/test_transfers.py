from booking import transfers

HEATHROW = (51.4700, -0.4543)
LONDON = (51.5074, -0.1278)


def test_distance_in_kilometres():
    km = transfers.distance_km(HEATHROW, LONDON)
    assert 20 < km < 26


def test_saloon_fare_for_the_airport_run():
    pence = transfers.fare(HEATHROW, LONDON, "saloon")
    assert pence > 4_000_000


def test_duration_is_returned_in_minutes():
    minutes = transfers.duration_minutes(HEATHROW, LONDON, "saloon")
    assert minutes > 400


def test_round_to_pound():
    assert transfers.round_to_pound(1250) == 1200
