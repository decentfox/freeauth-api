from __future__ import annotations

import string
from http import HTTPStatus
from typing import Dict

import edgedb
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from ...admin.tests.test_users_api import create_user
from ...config import get_settings
from ...queries.query_api import (
    AuthAuditEventType,
    AuthCodeType,
    AuthVerifyType,
    send_code,
    validate_code,
)
from ...utils import gen_random_string


def test_send_sign_up_code(test_client: TestClient):
    data: Dict = {}
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"
    assert error["detail"]["errors"]["code_type"] == "该字段为必填项"

    data = dict(
        account="user@example.com",
        code_type=AuthCodeType.EMAIL.value,
    )
    resp = test_client.post("/sign_up/code", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.OK, resp_data
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == AuthVerifyType.SIGNUP.value

    data = dict(
        account="13800000000",
        code_type=AuthCodeType.SMS.value,
    )
    resp = test_client.post("/sign_up/code", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.OK, resp_data
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == AuthVerifyType.SIGNUP.value

    data["account"] = "invalid-account"
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "仅支持中国大陆11位手机号"

    data["code_type"] = AuthCodeType.EMAIL.value
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "邮箱格式有误"

    data["code_type"] = "InvalidType"
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["code_type"] == "不是有效的枚举值"
    assert error["detail"]["errors"]["account"] == "手机号码或邮箱格式有误"

    create_user(
        test_client,
        email="user@example.com",
        mobile="13800000000",
    )
    data = dict(
        account="13800000000",
        code_type=AuthCodeType.SMS.value,
    )
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该账号已注册，请直接登录"

    data = dict(
        account="user@example.com",
        code_type=AuthCodeType.EMAIL.value,
    )
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该账号已注册，请直接登录"

    data["account"] = "user1@example.com"
    resp = test_client.post("/sign_up/code", json=data)
    record = resp.json()
    assert resp.status_code == HTTPStatus.OK, record
    assert record["account"] == data["account"]
    assert record["verify_type"] == AuthVerifyType.SIGNUP.value


@pytest.mark.parametrize(
    "data,errors",
    [
        (
            {},
            {
                "account": "该字段为必填项",
                "code": "该字段为必填项",
                "code_type": "该字段为必填项",
            },
        ),
        (
            {
                "code": "12345678",
                "code_type": "InvalidType",
                "account": "invalid-account",
            },
            {
                "code_type": "不是有效的枚举值",
                "account": "手机号码或邮箱格式有误",
            },
        ),
        (
            {
                "code": "12345678",
                "account": "user@example.com",
                "code_type": AuthCodeType.SMS.value,
            },
            {"account": "仅支持中国大陆11位手机号"},
        ),
        (
            {
                "code": "12345678",
                "account": "13800000000",
                "code_type": AuthCodeType.EMAIL.value,
            },
            {"account": "邮箱格式有误"},
        ),
        (
            {
                "code": "12345678",
                "account": "user@example.com",
                "code_type": AuthCodeType.EMAIL.value,
            },
            {"code": "验证码错误，请重新输入"},
        ),
        (
            {
                "code": "888888",
                "account": "13800000000",
                "code_type": AuthCodeType.SMS.value,
            },
            {"code": "验证码已失效，请重新获取"},
        ),
    ],
)
def test_validate_sign_up_code_failed(
    test_client: TestClient, data: Dict, errors: Dict
):
    settings = get_settings()
    if (
        data.get("account") in settings.demo_accounts
        and data.get("code") == settings.demo_code
    ):
        ttl, settings.verify_code_ttl = settings.verify_code_ttl, -1
        test_client.post(
            "/sign_up/code",
            json={"account": data["account"], "code_type": data["code_type"]},
        )
        settings.verify_code_ttl = ttl

    resp = test_client.post("/sign_up/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"] == errors


def test_sign_up(test_client: TestClient):
    account: str = "13800000000"
    create_user(
        test_client,
        mobile=account,
    )

    data: Dict = {
        "account": account,
        "code": "123123",
        "code_type": AuthCodeType.SMS.value,
    }
    resp = test_client.post("/sign_up/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该账号已注册，请直接登录"

    account = "user@example.com"
    test_client.post(
        "/sign_up/code",
        json={
            "account": account,
            "code_type": AuthCodeType.EMAIL.value,
        },
    )
    data: Dict = {
        "account": account,
        "code": "888888",
        "code_type": AuthCodeType.EMAIL.value,
    }
    resp = test_client.post("/sign_up/verify", json=data)
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

    resp = test_client.post("/audit_logs/query", json={})
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["rows"]) == 2
    assert rv["rows"][0]["event_type"] == AuthAuditEventType.SIGNIN.value
    assert rv["rows"][1]["event_type"] == AuthAuditEventType.SIGNUP.value


async def test_validate_code(edgedb_client: edgedb.AsyncIOClient):
    account: str = "13800000000"

    rv = await validate_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code="12345678",
    )
    assert not rv.code_found
    assert not rv.code_valid

    code: str = gen_random_string(6, letters=string.digits)
    await send_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
        ttl=-1,
    )

    rv = await validate_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
    )
    assert rv.code_found
    assert not rv.code_valid

    code: str = gen_random_string(6, letters=string.digits)
    await send_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
        ttl=300,
    )

    rv = await validate_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
    )
    assert rv.code_found
    assert rv.code_valid

    rv = await validate_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
    )
    assert not rv.code_found
    assert not rv.code_valid
