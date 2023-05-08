from __future__ import annotations

import time
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from ...config import get_config
from ...query_api import AuthCodeType
from ...users.tests.test_api import create_user
from .. import get_login_settings


@pytest.mark.parametrize(
    "signup_modes,data,err_msg",
    [
        (
            [],
            dict(
                account="13800000000",
                code_type=AuthCodeType.SMS.value,
            ),
            "系统不支持注册，如您已有账号，请直接登录",
        ),
        (
            ["mobile"],
            dict(
                account="user@example.com",
                code_type=AuthCodeType.EMAIL.value,
            ),
            "不支持邮箱和验证码注册",
        ),
        (
            ["email"],
            dict(
                account="13800000000",
                code_type=AuthCodeType.SMS.value,
            ),
            "不支持手机号和验证码注册",
        ),
    ],
)
def test_signup_modes(
    test_client: TestClient, signup_modes: list[str], data: dict, err_msg: str
):
    get_login_settings.cache_clear()
    resp = test_client.put(
        "/v1/login_settings", json={"signupModes": signup_modes}
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.post("/v1/sign_up/code", json=data)
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
    test_client: TestClient,
    code_signin_modes: list[str],
    data: dict,
    err_msg: str,
):
    get_login_settings.cache_clear()
    resp = test_client.put(
        "/v1/login_settings",
        json={"codeSigninModes": code_signin_modes},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.post("/v1/sign_in/code", json=data)
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
    test_client: TestClient,
    pwd_signin_modes: list[str],
    data: dict,
    err_msg: str,
):
    get_login_settings.cache_clear()
    resp = test_client.put(
        "/v1/login_settings",
        json={"pwdSigninModes": pwd_signin_modes},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    create_user(
        test_client,
        username="user",
        mobile="13800000000",
        email="user@example.com",
    )
    resp = test_client.post("/v1/sign_in", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == err_msg


@pytest.mark.parametrize(
    "jwt_token_ttl",
    [
        1440,
        30,
        0,
    ],
)
def test_jwt_token_ttl(test_client: TestClient, jwt_token_ttl: int):
    get_login_settings.cache_clear()
    resp = test_client.put(
        "/v1/login_settings",
        json={"jwtTokenTtl": jwt_token_ttl},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.post(
        "/v1/sign_up/code",
        json=dict(
            account="13800000000",
            code_type=AuthCodeType.SMS.value,
        ),
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = test_client.post(
        "/v1/sign_up/verify",
        json=dict(
            account="13800000000",
            code_type=AuthCodeType.SMS.value,
            code="888888",
        ),
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    config = get_config()
    req_set_cookie = resp.headers.get("Set-Cookie")
    assert config.jwt_cookie_key in req_set_cookie
    if jwt_token_ttl:
        assert f"Max-Age={jwt_token_ttl * 60}" in req_set_cookie
    else:
        assert "Max-Age" not in req_set_cookie

    token = resp.cookies.get(config.jwt_cookie_key)
    assert token is not None
    payload = jwt.decode(
        token, config.jwt_secret_key, algorithms=[config.jwt_algorithm]
    )
    assert (
        round((payload["exp"] - time.time()) / 60) == jwt_token_ttl
        or config.jwt_token_ttl
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
                "code_type": AuthCodeType.SMS.value,
            },
        ),
        ("signin", "sign_in", {"account": "13800000000", "code": "12345678"}),
    ],
)
def test_code_validating_limit(
    test_client: TestClient, limit_type: str, ep: str, data: dict
):
    if limit_type == "signin":
        create_user(
            test_client,
            email="user@example.com",
            mobile="13800000000",
        )
    get_login_settings.cache_clear()
    resp = test_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeValidatingLimitEnabled": False},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["code"] == "验证码错误或已失效，请重新获取"
    )

    code_data: dict = {"account": "13800000000"}
    if limit_type == "signup":
        code_data["code_type"] = AuthCodeType.SMS.value
    resp = test_client.post(f"/v1/{ep}/code", json=code_data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    for i in range(5):
        resp = test_client.post(f"/v1/{ep}/verify", json=data)
        error = resp.json()
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
        assert error["detail"]["errors"]["code"] == "验证码错误，请重新输入"

    resp = test_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeValidatingLimitEnabled": True},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = test_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeValidatingLimit": [2, 5]},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["code"] == "验证码错误，请重新输入"

    resp = test_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["code"]
        == "您输入的错误验证码次数过多，当前验证码已失效，请重新获取"
    )

    data["code"] = "888888"
    resp = test_client.post(f"/v1/{ep}/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["code"] == "验证码已失效，请重新获取"


@pytest.mark.parametrize(
    "limit_type,ep,data",
    [
        (
            "signup",
            "sign_up",
            {"account": "13800000000", "code_type": AuthCodeType.SMS.value},
        ),
        ("signin", "sign_in", {"account": "13800000000"}),
    ],
)
def test_code_sending_limit(
    test_client: TestClient, limit_type: str, ep: str, data: dict
):
    if limit_type == "signin":
        create_user(
            test_client,
            email="user@example.com",
            mobile="13800000000",
        )
    get_login_settings.cache_clear()
    resp = test_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeSendingLimitEnabled": False},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    for i in range(5):
        resp = test_client.post(f"/v1/{ep}/code", json=data)
        assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeSendingLimitEnabled": True},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = test_client.put(
        "/v1/login_settings",
        json={f"{limit_type}CodeSendingLimit": [3, 5]},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.post(f"/v1/{ep}/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["code"]
        == "验证码获取次数超限，请稍后再次获取"
    )
