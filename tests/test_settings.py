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

import os

from freeauth.conf.settings import get_settings


def test_get_settings_with_environ():
    os.environ["EDGEDB_DATABASE"] = "testdb"
    os.environ["DEBUG"] = "true"

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.edgedb_database == "testdb"
    assert settings.debug is True


def test_get_settings_from_env_file():
    with open(".env", "w") as f:
        f.write("FOO=bar\nDEBUG=false\nEDGEDB_DATABASE=freeauth")

    get_settings.cache_clear()
    settings = get_settings()
    os.remove(f.name)

    assert settings.edgedb_database == "freeauth"
    assert settings.debug is False
    assert os.environ["EDGEDB_DATABASE"] == settings.edgedb_database
