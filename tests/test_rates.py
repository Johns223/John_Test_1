from booking import rates


def test_seven_nights_uses_one_band():
    assert rates.nightly_total("standard", 7) == 49840


def test_five_nights_pays_cleaning():
    assert rates.cleaning_fee(5) == rates.CLEANING_FEE


def test_deposit_is_twenty_percent():
    assert rates.deposit_due(10000) == 2000


def test_instalments_lose_remainder():
    assert sum(rates.split_instalments(10000, 3)) == 9999
