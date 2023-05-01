from __future__ import annotations

from http import HTTPStatus
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from ...config import get_config
from ...query_api import AuthAuditEventType, AuthCodeType, AuthVerifyType
from ...users.tests.test_api import create_user


@pytest.fixture(autouse=True)
def login_settings_for_signup(test_client: TestClient):
    # enable all signup modes
    test_client.put(
        "/v1/login_settings/code_signin_modes",
        json={"value": ["mobile", "email"]},
    )
    test_client.put(
        "/v1/login_settings/pwd_signin_modes",
        json={"value": ["username", "mobile", "email"]},
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
    config = get_config()
    if data.get("account") == "13800000000":
        if data.get("code") == config.demo_code:
            test_client.put(
                "/v1/login_settings/signin_code_validating_limit",
                json={"value": [3, -1]},
            )
        test_client.post("/v1/sign_in/code", json={"account": data["account"]})
        test_client.put(
            "/v1/login_settings/signin_code_validating_limit",
            json={"value": [3, 10]},
        )

    resp = test_client.post("/v1/sign_in/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"] == errors


def test_sign_in_with_code(test_client: TestClient):
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

    config = get_config()
    token = resp.cookies.get(config.jwt_cookie_key)
    assert token is not None
    payload = jwt.decode(
        token, config.jwt_secret_key, algorithms=[config.jwt_algorithm]
    )
    assert payload["sub"] == user["id"]

    resp = test_client.post("/v1/audit_logs/query", json={})
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["rows"]) == 1
    assert rv["rows"][0]["event_type"] == AuthAuditEventType.SIGNIN.value
    assert rv["rows"][0]["status_code"] == HTTPStatus.OK
    assert rv["rows"][0]["user"]["email"] == account
    assert rv["rows"][0]["os"] == "Mac OS X"


async def test_sign_in_with_password(test_client: TestClient):
    resp = test_client.post("/v1/sign_in", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"
    assert error["detail"]["errors"]["password"] == "该字段为必填项"

    account: str = "13800000000"
    data: Dict = {
        "account": account,
        "password": "123123",
    }
    resp = test_client.post("/v1/sign_in", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["account"]
        == "账号不存在，请您确认登录信息输入是否正确"
    )

    # TODO: complete this test
