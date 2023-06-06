from __future__ import annotations

from http import HTTPStatus
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from freeauth.conf.settings import get_settings
from freeauth.db.auth.auth_qry_async_edgeql import (
    AuthAuditStatusCode,
    AuthCodeType,
    AuthVerifyType,
)
from freeauth.security.utils import gen_random_string

from ...audit_logs.dataclasses import AuthAuditEventType
from ...users.tests.test_api import create_user


@pytest.fixture(autouse=True)
def login_settings_for_signup(bo_client: TestClient):
    # enable all signup & signin modes
    bo_client.put(
        "/v1/login_settings",
        json={
            "codeSigninModes": ["mobile", "email"],
            "pwdSigninModes": ["username", "mobile", "email"],
            "signinCodeValidatingLimitEnabled": True,
            "signinPwdValidatingLimitEnabled": True,
            "signinPwdValidatingMaxAttempts": 2,
        },
    )


def test_send_sign_in_code(test_client: TestClient):
    data: Dict = {}
    resp = test_client.post("/v1/sign_in/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"

    data["account"] = "invalid_account"
    resp = test_client.post("/v1/sign_in/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "手机号码或邮箱格式有误"

    data["account"] = "user@example.com"
    resp = test_client.post("/v1/sign_in/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["account"]
        == "账号不存在，请您确认登录信息输入是否正确"
    )

    user = create_user(
        test_client,
        email="user@example.com",
    )
    resp = test_client.put(
        "/v1/users/status",
        json={
            "user_ids": [str(user.id)],
            "is_deleted": True,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = test_client.post("/v1/sign_in/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "您的账号已停用"

    user = create_user(
        test_client,
        mobile="13800000000",
    )
    data["account"] = "13800000000"
    resp = test_client.post("/v1/sign_in/code", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.OK, resp_data
    assert resp_data["account"] == user.mobile
    assert resp_data["code_type"] == AuthCodeType.SMS.value
    assert resp_data["verify_type"] == AuthVerifyType.SIGNIN.value


@pytest.mark.parametrize(
    "data,errors",
    [
        (
            {},
            {
                "account": "该字段为必填项",
                "code": "该字段为必填项",
            },
        ),
        (
            {
                "code": "12345678",
                "account": "invalid-account",
            },
            {
                "account": "手机号码或邮箱格式有误",
            },
        ),
        (
            {
                "code": "12345678",
                "account": "user@example.com",
            },
            {"code": "验证码错误或已失效，请重新获取"},
        ),
        (
            {
                "code": "12345678",
                "account": "13800000000",
            },
            {"code": "验证码错误，请重新输入"},
        ),
        (
            {
                "code": "888888",
                "account": "13800000000",
            },
            {"code": "验证码已失效，请重新获取"},
        ),
    ],
)
def test_validate_sign_in_code_failed(
    test_client: TestClient, data: Dict, errors: Dict
):
    create_user(
        test_client,
        email="user@example.com",
        mobile="13800000000",
    )
    settings = get_settings()
    if data.get("account") == "13800000000":
        if data.get("code") == settings.demo_code:
            test_client.put(
                "/v1/login_settings",
                json={
                    "signinCodeValidatingInterval": -1,
                },
            )
        test_client.post("/v1/sign_in/code", json={"account": data["account"]})
        test_client.put(
            "/v1/login_settings",
            json={
                "signinCodeValidatingInterval": 10,
            },
        )

    resp = test_client.post("/v1/sign_in/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"] == errors


def test_sign_in_with_code(test_client: TestClient, bo_client: TestClient):
    account: str = "13800000000"
    data: Dict = {
        "account": account,
        "code": "123123",
    }
    resp = test_client.post("/v1/sign_in/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["account"]
        == "账号不存在，请您确认登录信息输入是否正确"
    )

    user = create_user(
        test_client,
        mobile=account,
    )
    resp = test_client.put(
        "/v1/users/status",
        json={
            "user_ids": [str(user.id)],
            "is_deleted": True,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = test_client.post("/v1/sign_in/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "您的账号已停用"

    account = "user@example.com"
    create_user(
        test_client,
        email=account,
    )
    test_client.post("/v1/sign_in/code", json={"account": account})
    data = {
        "account": account,
        "code": "888888",
    }
    resp = test_client.post("/v1/sign_in/verify", json=data)
    user = resp.json()
    assert resp.status_code == HTTPStatus.OK, user
    assert user["email"] == account
    assert user["last_login_at"] is not None

    settings = get_settings()
    token = resp.cookies.get(settings.jwt_cookie_key)
    assert token is not None
    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert payload["sub"] == user["id"]

    resp = test_client.post("/v1/audit_logs/query", json={"q": account})
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["rows"]) == 1
    assert rv["rows"][0]["event_type"] == AuthAuditEventType.SIGNIN.value
    assert (
        AuthAuditStatusCode(rv["rows"][0]["status_code"])
        == AuthAuditStatusCode.OK
    )
    assert rv["rows"][0]["is_succeed"]
    assert rv["rows"][0]["user"]["email"] == account
    assert rv["rows"][0]["os"] == "Mac OS X"


def test_sign_in_with_password(test_client: TestClient):
    resp = test_client.post("/v1/sign_in", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"
    assert error["detail"]["errors"]["password"] == "该字段为必填项"

    account: str = "13800000000"
    data: Dict = {
        "account": account,
        "password": "wrong password",
    }
    resp = test_client.post("/v1/sign_in", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert (
        error["detail"]["errors"]["account"]
        == "账号不存在，请您确认登录信息输入是否正确"
    )

    password = gen_random_string(12, secret=True)
    user = create_user(test_client, mobile="13800000000", password=password)
    resp = test_client.put(
        "/v1/users/status",
        json={
            "user_ids": [str(user.id)],
            "is_deleted": True,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = test_client.post("/v1/sign_in", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "您的账号已停用"

    resp = test_client.put(
        "/v1/users/status",
        json={
            "user_ids": [str(user.id)],
            "is_deleted": False,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    data["password"] = password
    resp = test_client.post("/v1/sign_in", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["mobile"] == user.mobile
    assert rv["last_login_at"]

    data["password"] = "wrong password"
    for _ in range(2):
        resp = test_client.post("/v1/sign_in", json=data)
        error = resp.json()
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
        assert error["detail"]["errors"]["password"] == "密码输入错误"

    resp = test_client.post("/v1/sign_in", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["password"]
        == "密码连续多次输入错误，账号暂时被锁定"
    )


def test_get_user_me(bo_client: TestClient, bo_user):
    resp = bo_client.get("/v1/me")
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["id"] == str(bo_user.id)

    resp = bo_client.put(
        "/v1/users/status",
        json={
            "user_ids": [str(bo_user.id)],
            "is_deleted": True,
        },
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    resp = bo_client.get("/v1/me")
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNAUTHORIZED, error
    assert "身份验证失败" in error["detail"]["message"]


def test_sign_out(bo_client: TestClient, bo_user):
    resp = bo_client.get("/v1/me")
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["id"] == str(bo_user.id)

    resp = bo_client.post("/v1/sign_out")
    assert resp.status_code == HTTPStatus.OK, resp.json()

    settings = get_settings()
    token = resp.cookies.get(settings.jwt_cookie_key)
    assert token is None

    resp = bo_client.get("/v1/me")
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNAUTHORIZED, error
    assert "身份验证失败" in error["detail"]["message"]
