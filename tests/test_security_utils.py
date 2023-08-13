# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan
# PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

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
