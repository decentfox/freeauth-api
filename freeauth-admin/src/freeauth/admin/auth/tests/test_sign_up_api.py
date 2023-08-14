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

import string
from http import HTTPStatus
from typing import Dict

import edgedb
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from freeauth.conf.settings import get_settings
from freeauth.db.auth.auth_qry_async_edgeql import (
    FreeauthAuditStatusCode,
    FreeauthCodeType,
    FreeauthVerifyType,
    send_code,
    validate_code,
)
from freeauth.security.utils import gen_random_string

from ...users.tests.test_api import create_user


@pytest.fixture(autouse=True)
def login_settings_for_signup(bo_client: TestClient):
    # enable all signup modes
    bo_client.put(
        "/v1/login_settings",
        json={
            "signupModes": ["mobile", "email"],
            "signupCodeValidatingLimitEnabled": True,
        },
    )


def test_send_sign_up_code(test_client: TestClient):
    data: Dict = {}
    resp = test_client.post("/v1/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"
    assert error["detail"]["errors"]["code_type"] == "该字段为必填项"

    data = dict(
        account="user@example.com",
        code_type=FreeauthCodeType.EMAIL.value,
    )
    resp = test_client.post("/v1/sign_up/code", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.OK, resp_data
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == FreeauthVerifyType.SIGNUP.value

    data = dict(
        account="13800000000",
        code_type=FreeauthCodeType.SMS.value,
    )
    resp = test_client.post("/v1/sign_up/code", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.OK, resp_data
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == FreeauthVerifyType.SIGNUP.value

    data["account"] = "invalid-account"
    resp = test_client.post("/v1/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "仅支持中国大陆11位手机号"

    data["code_type"] = FreeauthCodeType.EMAIL.value
    resp = test_client.post("/v1/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "邮箱格式有误"

    data["code_type"] = "InvalidType"
    resp = test_client.post("/v1/sign_up/code", json=data)
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
        code_type=FreeauthCodeType.SMS.value,
    )
    resp = test_client.post("/v1/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该账号已注册，请直接登录"

    data = dict(
        account="user@example.com",
        code_type=FreeauthCodeType.EMAIL.value,
    )
    resp = test_client.post("/v1/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该账号已注册，请直接登录"

    data["account"] = "user1@example.com"
    resp = test_client.post("/v1/sign_up/code", json=data)
    record = resp.json()
    assert resp.status_code == HTTPStatus.OK, record
    assert record["account"] == data["account"]
    assert record["verify_type"] == FreeauthVerifyType.SIGNUP.value


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
                "code_type": FreeauthCodeType.SMS.value,
            },
            {"account": "仅支持中国大陆11位手机号"},
        ),
        (
            {
                "code": "12345678",
                "account": "13800000000",
                "code_type": FreeauthCodeType.EMAIL.value,
            },
            {"account": "邮箱格式有误"},
        ),
        (
            {
                "code": "12345678",
                "account": "13800000001",
                "code_type": FreeauthCodeType.SMS.value,
            },
            {"code": "验证码错误或已失效，请重新获取"},
        ),
        (
            {
                "code": "12345678",
                "account": "13800000000",
                "code_type": FreeauthCodeType.SMS.value,
            },
            {"code": "验证码错误，请重新输入"},
        ),
        (
            {
                "code": "888888",
                "account": "13800000000",
                "code_type": FreeauthCodeType.SMS.value,
            },
            {"code": "验证码已失效，请重新获取"},
        ),
    ],
)
def test_validate_sign_up_code_failed(
    test_client: TestClient, data: Dict, errors: Dict
):
    settings = get_settings()
    if data.get("account") in settings.demo_accounts:
        if data.get("code") == settings.demo_code:
            test_client.put(
                "/v1/login_settings",
                json={
                    "signupCodeValidatingInterval": -1,
                },
            )
        test_client.post(
            "/v1/sign_up/code",
            json={"account": data["account"], "code_type": data["code_type"]},
        )
        test_client.put(
            "/v1/login_settings",
            json={
                "signupCodeValidatingInterval": 10,
            },
        )

    resp = test_client.post("/v1/sign_up/verify", json=data)
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
        "code_type": FreeauthCodeType.SMS.value,
    }
    resp = test_client.post("/v1/sign_up/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该账号已注册，请直接登录"

    account = "user@example.com"
    test_client.post(
        "/v1/sign_up/code",
        json={
            "account": account,
            "code_type": FreeauthCodeType.EMAIL.value,
        },
    )
    data: Dict = {
        "account": account,
        "code": "888888",
        "code_type": FreeauthCodeType.EMAIL.value,
    }
    resp = test_client.post("/v1/sign_up/verify", json=data)
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
    assert len(rv["rows"]) == 2


async def test_validate_code(edgedb_client: edgedb.AsyncIOClient):
    account: str = "13800000000"

    rv = await validate_code(
        edgedb_client,
        account=account,
        code_type=FreeauthCodeType.SMS,
        verify_type=FreeauthVerifyType.SIGNUP,
        code="12345678",
    )
    status_code = FreeauthAuditStatusCode(str(rv.status_code))
    assert status_code == FreeauthAuditStatusCode.INVALID_CODE

    code: str = gen_random_string(6, letters=string.digits)
    await send_code(
        edgedb_client,
        account=account,
        code_type=FreeauthCodeType.SMS,
        verify_type=FreeauthVerifyType.SIGNUP,
        code=code,
        ttl=300,
        max_attempts=3,
        attempts_ttl=60,
    )

    for i in range(3):
        rv = await validate_code(
            edgedb_client,
            account=account,
            code_type=FreeauthCodeType.SMS,
            verify_type=FreeauthVerifyType.SIGNUP,
            code="12345678",
            max_attempts=3,
        )
        status_code = FreeauthAuditStatusCode(str(rv.status_code))
        if i < 2:
            assert status_code == FreeauthAuditStatusCode.CODE_INCORRECT
        else:
            assert (
                status_code == FreeauthAuditStatusCode.CODE_ATTEMPTS_EXCEEDED
            )

    code: str = gen_random_string(6, letters=string.digits)
    await send_code(
        edgedb_client,
        account=account,
        code_type=FreeauthCodeType.SMS,
        verify_type=FreeauthVerifyType.SIGNIN,
        code=code,
        ttl=300,
        max_attempts=3,
        attempts_ttl=60,
    )

    rv = await validate_code(
        edgedb_client,
        account=account,
        code_type=FreeauthCodeType.SMS,
        verify_type=FreeauthVerifyType.SIGNIN,
        code="12345678",
        max_attempts=3,
    )
    status_code = FreeauthAuditStatusCode(str(rv.status_code))
    assert status_code == FreeauthAuditStatusCode.CODE_INCORRECT

    rv = await validate_code(
        edgedb_client,
        account=account,
        code_type=FreeauthCodeType.SMS,
        verify_type=FreeauthVerifyType.SIGNIN,
        code=code,
        max_attempts=3,
    )
    status_code = FreeauthAuditStatusCode(str(rv.status_code))
    assert status_code == FreeauthAuditStatusCode.OK
