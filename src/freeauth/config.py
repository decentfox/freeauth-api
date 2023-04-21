from __future__ import annotations

from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False

    verify_code_ttl: int = 300  # in seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
