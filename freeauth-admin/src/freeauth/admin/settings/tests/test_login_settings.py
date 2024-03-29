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

import time
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from freeauth.conf.settings import get_settings
from freeauth.db.auth.auth_qry_async_edgeql import FreeauthCodeType
from freeauth.security.utils import gen_random_string

from ...users.tests.test_api import create_user


@pytest.mark.parametrize(
    "signup_modes,data,err_msg",
    [
        (
            [],
            dict(
                account="13800000000",
                code_type=FreeauthCodeType.SMS.value,
            ),
            "系统不支持注册，如您已有账号，请直接登录",
        ),
        (
            ["mobile"],
            dict(
                account="user@example.com",
                code_type=FreeauthCodeType.EMAIL.value,
            ),
            "不支持邮箱和验证码注册",
        ),
        (
            ["email"],
            dict(
                account="13800000000",
                code_type=FreeauthCodeType.SMS.value,
            ),
            "不支持手机号和验证码注册",
        ),
    ],
)
def test_signup_modes(
    bo_client: TestClient, signup_modes: list[str], data: dict, err_msg: str
):
    resp = bo_client.put(
        "/v1/login_settings", json={"signupModes": signup_modes}
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = bo_client.post("/v1/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["code_type"] == err_msg


@pytest.mark.parametrize(
    "code_signin_modes,data,err_msg",
    [
        (
            [],
            dict(
                account="13800000000",
            ),
            "系统不支持验证码登录，请使用其他登录方式",
        ),
        (
            ["mobile"],
            dict(
                account="user@example.com",
            ),
            "不支持邮箱和验证码登录",
        ),
        (
            ["email"],
            dict(
                account="13800000000",
            ),
            "不支持手机号和验证码登录",
        ),
    ],
)
def test_code_signin_modes(
    bo_client: TestClient,
    code_signin_modes: list[str],
    data: dict,
    err_msg: str,
):
    resp = bo_client.put(
        "/v1/login_settings",
        json={"codeSigninModes": code_signin_modes},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = bo_client.post("/v1/sign_in/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == err_msg


@pytest.mark.parametrize(
    "pwd_signin_modes,data,err_msg",
    [
        (
            [],
            dict(account="user", password="123123"),
            "系统不支持密码登录，请使用其他登录方式",
        ),
        (
            ["mobile", "email"],
            dict(account="user", password="123123"),
            "账号不存在，请您确认登录信息输入是否正确",
        ),
        (
            ["username", "email"],
            dict(account="13800000000", password="123123"),
            "账号不存在，请您确认登录信息输入是否正确",
        ),
        (
            ["username", "mobile"],
            dict(account="user@example.com", password="123123"),
            "账号不存在，请您确认登录信息输入是否正确",
        ),
    ],
)
def test_pwd_signin_modes(
    bo_client: TestClient,
    pwd_signin_modes: list[str],
    data: dict,
    err_msg: str,
):
    resp = bo_client.put(
        "/v1/login_settings",
        json={"pwdSigninModes": pwd_signin_modes},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    create_user(
        bo_client,
        username="user",
        mobile="13800000000",
        email="user@example.com",
    )
    resp = bo_client.post("/v1/sign_in", json=data)
    error = resp.json()
    if not pwd_signin_modes:
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    else:
        assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["errors"]["account"] == err_msg


@pytest.mark.parametrize(
    "jwt_token_ttl",
    [
        1440,
        30,
        0,
    ],
)
def test_jwt_token_ttl(bo_client: TestClient, jwt_token_ttl: int):
    resp = bo_client.put(
        "/v1/login_settings",
        json={"jwtTokenTtl": jwt_token_ttl},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = bo_client.post(
        "/v1/sign_up/code",
        json=dict(
            account="13800000000",
            code_type=FreeauthCodeType.SMS.value,
        ),
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = bo_client.post(
        "/v1/sign_up/verify",
        json=dict(
            account="13800000000",
            code_type=FreeauthCodeType.SMS.value,
            code="888888",
        ),
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    settings = get_settings()
    req_set_cookie = resp.headers.get("Set-Cookie")
    assert settings.jwt_cookie_key in req_set_cookie
    if jwt_token_ttl:
        assert f"Max-Age={jwt_token_ttl * 60}" in req_set_cookie
    else:
        assert "Max-Age" not in req_set_cookie

    token = resp.cookies.get(settings.jwt_cookie_key)
    assert token is not None
    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert (
        round((payload["exp"] - time.time()) / 60) == jwt_token_ttl
        or settings.jwt_token_ttl
    )


@pytest.mark.parametrize(
    "limit_type,ep,data",
    [
        (
            "signup",
            "sign_up",
            {
                "account": "13800000000",
                "code": "12345678",
                "code_type": FreeauthCodeType.SMS.value,
            },
        ),
        ("signin", "sign_in", {"account": "13800000000", "code": "12345678"}),
    ],
)
def test_code_validating_limit(
    bo_client: TestClient, limit_type: str, ep: str, data: dict
):
    if limit_type == "signin":
        create_user(
            bo_client,
            email="user@example.com",
            mobile="13800000000",
        )
    resp = bo_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeValidatingLimitEnabled": False},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = bo_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["code"] == "验证码错误或已失效，请重新获取"
    )

    code_data: dict = {"account": "13800000000"}
    if limit_type == "signup":
        code_data["code_type"] = FreeauthCodeType.SMS.value
    resp = bo_client.post(f"/v1/{ep}/code", json=code_data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    for i in range(5):
        resp = bo_client.post(f"/v1/{ep}/verify", json=data)
        error = resp.json()
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
        assert error["detail"]["errors"]["code"] == "验证码错误，请重新输入"

    resp = bo_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeValidatingLimitEnabled": True},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = bo_client.put(
        "/v1/login_settings",
        json={
            f"{limit_type}CodeValidatingMaxAttempts": 2,
            f"{limit_type}CodeValidatingInterval": 5,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = bo_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["code"] == "验证码错误，请重新输入"

    resp = bo_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["code"]
        == "您输入的错误验证码次数过多，当前验证码已失效，请重新获取"
    )

    data["code"] = "888888"
    resp = bo_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["code"] == "验证码已失效，请重新获取"


@pytest.mark.parametrize(
    "limit_type,ep,data",
    [
        (
            "signup",
            "sign_up",
            {
                "account": "13800000000",
                "code_type": FreeauthCodeType.SMS.value,
            },
        ),
        ("signin", "sign_in", {"account": "13800000000"}),
    ],
)
def test_code_sending_limit(
    bo_client: TestClient, limit_type: str, ep: str, data: dict
):
    if limit_type == "signin":
        create_user(
            bo_client,
            email="user@example.com",
            mobile="13800000000",
        )
    resp = bo_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeSendingLimitEnabled": False},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    for i in range(5):
        resp = bo_client.post(f"/v1/{ep}/code", json=data)
        assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = bo_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeSendingLimitEnabled": True},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = bo_client.put(
        "/v1/login_settings",
        json={
            f"{limit_type}CodeSendingMaxAttempts": 3,
            f"{limit_type}CodeSendingInterval": 5,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = bo_client.post(f"/v1/{ep}/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["code"]
        == "验证码获取次数超限，请稍后再次获取"
    )


def test_pwd_validating_limit(bo_client: TestClient):
    password = gen_random_string(12, secret=True)
    user = create_user(bo_client, mobile="13800000000", password=password)

    resp = bo_client.put(
        "/v1/login_settings",
        json={
            "signinPwdValidatingLimitEnabled": False,
            "signinPwdValidatingMaxAttempts": 3,
            "signinPwdValidatingInterval": 1440,
            "pwdSigninModes": ["mobile"],
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    for i in range(4):
        resp = bo_client.post(
            "/v1/sign_in",
            json={"account": user.mobile, "password": "wrong password"},
        )
        error = resp.json()
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
        assert error["detail"]["errors"]["password"] == "密码输入错误"

    resp = bo_client.put(
        "/v1/login_settings",
        json={
            "signinPwdValidatingLimitEnabled": True,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = bo_client.post(
        "/v1/sign_in",
        json={"account": user.mobile, "password": "wrong password"},
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["password"]
        == "密码连续多次输入错误，账号暂时被锁定"
    )
