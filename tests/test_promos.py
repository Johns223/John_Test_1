from booking import promos


def setup_function():
    promos._REDEMPTIONS.clear()


def test_signature_round_trips():
    code = "SPRING26"
    assert promos.verify_signature(code, promos.sign(code)) is True


def test_generated_code_is_the_right_length():
    assert len(promos.generate_code()) == promos.CODE_LENGTH


def test_another_customer_counts_as_redeemed():
    promos._REDEMPTIONS.append({"customer_id": "cust-a", "code": "SPRING26"})
    assert promos.already_redeemed("cust-b", "SPRING26") is True
