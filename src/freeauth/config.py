from __future__ import annotations

from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    testing: bool = False

    jwt_algorithm: str = "HS256"
    jwt_token_ttl: int = 1440  # 分钟，默认为一天
    jwt_secret_key: str = "secret_key"
    jwt_cookie_key: str = "access_token"

    verify_code_ttl: int = 300  # in minutes
    verify_code_cool_down: int = 60  # in seconds
    demo_code: str = "888888"
    demo_accounts: list[str] = []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
