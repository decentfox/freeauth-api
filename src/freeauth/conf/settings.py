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
import uuid
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    testing: bool = False

    edgedb_instance: str | None
    edgedb_dsn: str | None
    edgedb_database: str = "edgedb"

    freeauth_app_id: uuid.UUID | None

    jwt_algorithm: str = "HS256"
    jwt_token_ttl: int = 1440  # 分钟，默认为一天
    jwt_secret_key: str = "secret_key"
    jwt_cookie_key: str = "access_token"
    jwt_cookie_secure: bool = True

    verify_code_ttl: int = 10  # in minutes
    verify_code_cool_down: int = 60  # in seconds
    demo_code: str = "888888"
    demo_accounts: list[str] = []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orig_env = os.environ
        env = orig_env.copy()
        for name in self.__fields__:
            if not name.startswith("edgedb_"):
                continue
            value = getattr(self, name)
            if value is not None:
                env[name.upper()] = value
        os.environ = env


@lru_cache()
def get_settings() -> Settings:
    return Settings()
