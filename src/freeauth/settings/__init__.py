from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import edgedb

from ..query_api import (
    GetLoginSettingResult,
    get_login_setting,
    get_login_setting_by_key,
    upsert_login_setting,
)


class _None:
    pass


class LoginSettings:
    # Guard
    guard_logo: str | None = None  # 自定义 logo 图片地址
    guard_title: str = "自定义标题"  # 自定义标题
    guard_primary_color: str = "#215ae5"  # 自定义界面主色
    agreement_enabled: bool = False  # 是否开启登录注册协议
    agreement_title: str = "我已阅读并同意隐私协议与服务条款"  # 协议勾选框文字
    agreement_link: str | None = None  # 协议跳转链接

    # Signup
    signup_modes: list[str] = [
        "mobile",  # 支持手机号和验证码注册
        # "email",  # 支持邮箱和验证码注册
    ]  # 注册方式，`[]` 代表不支持用户自主注册
    signup_code_validating_limit_enabled: bool = (
        False  # 是否限制注册验证码尝试次数
    )
    # 同一注册验证码在指定周期内允许输入错误的次数，3次/10分钟
    signup_code_validating_max_attempts: int = 3
    signup_code_validating_interval: int = 10
    signup_code_sending_limit_enabled: bool = (
        False  # 是否限制注册验证码发送次数
    )
    # 同一账号在指定周期内允许获取注册验证码的次数，5次/60分钟
    signup_code_sending_max_attempts: int = 5
    signup_code_sending_interval: int = 60
    change_pwd_after_first_login_enabled: bool = (
        False  # 注册后首次登录是否强制要求修改密码
    )

    # Signin
    code_signin_modes: list[str] = [
        "mobile",  # 支持手机号和验证码登录
        # "email",  # 支持邮箱和验证码登录
    ]  # 验证码登录方式，`[]` 代表不支持验证码登录
    signin_code_validating_limit_enabled: bool = (
        False  # 是否限制登录验证码尝试次数
    )
    # 同一登录验证码在指定周期内允许输入错误的次数，3次/10分钟
    signin_code_validating_max_attempts: int = 3
    signin_code_validating_interval: int = 10
    signin_code_sending_limit_enabled: bool = (
        False  # 是否限制登录验证码发送次数
    )
    # 同一账号在指定周期内允许获取登录验证码的次数，5次/60分钟
    signin_code_sending_max_attempts: int = 5
    signin_code_sending_interval: int = 60
    pwd_signin_modes: list[str] = [
        # "username",  # 支持用户名登录
        # "mobile",  # 支持手机号登录
        # "email",  # 支持邮箱登录
    ]  # 密码登录方式，`[]` 代表不支持密码登录
    signin_pwd_validating_limit_enabled: bool = (
        False  # 是否限制登录密码尝试次数
    )
    # 同一登录密码在指定周期内允许输入错误的次数，5次/1440分钟（1天）
    signin_pwd_validating_max_attempts: int = 5
    signin_pwd_validating_interval: int = 1440
    jwt_token_ttl: int = 0  # 分钟，默认关闭浏览器即过期

    def __init__(self):
        self._cache = {}
        self._empty = True

    def get_keys(self):
        return [
            x
            for x in dir(self)
            if not callable(getattr(self, x)) and not x.startswith("_")
        ]

    async def get(self, key: str, client: edgedb.AsyncIOClient, load_all=True):
        if load_all and self._empty:
            await self.get_all(client)

        value = self._cache.get(key, _None)
        if value is _None:
            item: GetLoginSettingResult | None = None
            if self._empty:
                item = await get_login_setting_by_key(client, key=key)
            if item is None:
                value = getattr(self, key, None)
            else:
                value = json.loads(item.value)
                self._cache[key] = value
        return value

    async def get_all(self, client: edgedb.AsyncIOClient):
        if self._empty:
            self._empty = False
            for key in self.get_keys():
                self._cache[key] = getattr(self, key, None)
            items: list[GetLoginSettingResult] = await get_login_setting(
                client
            )
            for item_in_db in items:
                if item_in_db.key in self._cache:
                    self._cache[item_in_db.key] = json.loads(item_in_db.value)
        return self._cache

    async def patch(
        self, configs: dict[str, Any], client: edgedb.AsyncIOClient
    ):
        await upsert_login_setting(client, configs=json.dumps(configs))
        for key, value in configs.items():
            self._cache[key] = value


@lru_cache()
def get_login_settings() -> LoginSettings:
    return LoginSettings()
