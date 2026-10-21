from bosquevivo.core.privacy import phone_hmac


def test_phone_hmac_is_stable_and_ignores_formatting():
    a = phone_hmac("+57 300 123 4567", "k")
    b = phone_hmac("573001234567", "k")
    assert a == b
    assert "573001234567" not in a


def test_phone_hmac_depends_on_key():
    assert phone_hmac("573001234567", "a") != phone_hmac("573001234567", "b")
