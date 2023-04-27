from __future__ import annotations

import json
from functools import lru_cache

import edgedb

from ..queries.query_api import (
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
    signup_code_validating_limit: list[int] = [
        3,
        10,
    ]  # 次/分钟，同一注册验证码在指定周期内允许输入错误的次数
    signup_code_sending_limit_enabled: bool = (
        False  # 是否限制注册验证码发送次数
    )
    signup_code_sending_limit: list[int] = [
        5,
        60,
    ]  # 次/分钟，同一账号在指定周期内允许获取注册验证码的次数
    change_pwd_after_first_login_enabled: bool = (
        False  # 注册后首次登录是否强制要求设置用户名及密码
    )

    # Signin
    code_signin_modes: list[str] = [
        "mobile",  # 支持手机号和验证码登录
        # "email",  # 支持邮箱和验证码登录
    ]  # 验证码登录方式，`[]` 代表不支持验证码登录
    signin_code_validating_limit_enabled: bool = (
        False  # 是否限制登录验证码尝试次数
    )
    signin_code_validating_limit: list[int] = [
        3,
        10,
    ]  # 次/分钟，同一登录验证码在指定周期内允许输入错误的次数
    signin_code_sending_limit_enabled: bool = (
        False  # 是否限制登录验证码发送次数
    )
    signin_code_sending_limit: list[int] = [
        5,
        60,
    ]  # 次/分钟，同一账号在指定周期内允许获取登录验证码的次数
    pwd_signin_modes: list[str] = [
        # "username",  # 支持用户名登录
        # "mobile",  # 支持手机号登录
        # "email",  # 支持邮箱登录
    ]  # 密码登录方式，`[]` 代表不支持密码登录
    jwt_token_ttl: int = 0  # 分钟，默认关闭浏览器即过期

    def __init__(self):
        self._cache = {}
        self._empty = True

    async def get(self, key: str, client: edgedb.AsyncIOClient, load_all=True):
        default_val = getattr(self.__class__, key, None)
        if load_all and self._empty:
            self._empty = False
            items: list[GetLoginSettingResult] = await get_login_setting(
                client
            )
            for item_in_db in items:
                self._cache[item_in_db.key] = json.loads(item_in_db.value)
        value = self._cache.get(key, _None)
        if value is _None:
            item: GetLoginSettingResult | None = None
            if self._empty:
                item = await get_login_setting_by_key(client, key=key)
            if item is None:
                value = default_val
            else:
                value = json.loads(item.value)
                self._cache[key] = value
        return value

    async def set(self, key: str, value, client: edgedb.AsyncIOClient):
        item: GetLoginSettingResult = await upsert_login_setting(
            client, key=key, value=json.dumps(value)
        )
        self._cache[item.key] = value
        return {key: value}


@lru_cache()
def get_login_settings() -> LoginSettings:
    return LoginSettings()
