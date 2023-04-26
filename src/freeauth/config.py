from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    testing: bool = False

    jwt_algorithm: str = "HS256"
    jwt_token_ttl: int = 1440  # 分钟，默认为一天
    jwt_secret_key: str = "secret_key"
    jwt_cookie_key: str = "access_token"

    # Signup
    code_signup_modes: List[str] = [
        "mobile",  # 支持手机号注册
        # "email",  # 支持邮箱注册
    ]  # 当启用验证码注册时，所支持的方式，`[]` 则代表不支持验证码注册
    signup_code_validating_limit: Tuple[int, int] = (
        3,
        10,
    )  # 次/分钟，同一注册验证码在指定周期内允许输入错误的次数
    signup_code_sending_limit: Tuple[int, int] = (
        5,
        60,
    )  # 次/分钟，同一账号在指定周期内允许获取注册验证码的次数
    force_to_change_pwd_after_first_login: bool = (
        False  # 注册后首次登录是否强制要求设置用户名及密码
    )

    # Signin
    code_signin_modes: List[str] = [
        "mobile",  # 支持手机号登录
        # "email",  # 支持邮箱登录
    ]  # 当启用验证码登录时，所支持的方式，`[]` 则代表不支持验证码登录
    signin_code_validating_limit: Tuple[int, int] = (
        3,
        10,
    )  # 次/分钟，同一登录验证码在指定周期内允许输入错误的次数
    signin_code_sending_limit: Tuple[int, int] = (
        5,
        60,
    )  # 次/分钟，同一账号在指定周期内允许获取登录验证码的次数
    pwd_signin_modes: List[str] = [
        # "username",  # 支持用户名登录
        # "mobile",  # 支持手机号登录
        # "email",  # 支持邮箱登录
    ]  # 当启用密码登录时，所支持的方式，`[]` 则代表不支持密码登录

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
