from __future__ import annotations

import string

from freeauth.security.utils import (
    gen_random_string,
    get_password_hash,
    verify_password,
)


def test_generate_random_string():
    generated = gen_random_string(size=10)
    assert len(generated) == 10

    generated = gen_random_string(size=30, letters=string.ascii_uppercase)
    assert generated.upper() == generated

    generated = gen_random_string(size=8, letters=string.digits, secret=True)
    for c in generated:
        assert c in string.digits


def test_password_hash():
    hashed_password = get_password_hash("123456")
    assert not verify_password("123123", hashed_password)
    assert verify_password("123456", hashed_password)
