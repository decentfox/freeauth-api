from __future__ import annotations

import string
from http import HTTPStatus
from typing import Dict

import edgedb
import pytest
from fastapi.testclient import TestClient

from ...queries.query_api import (
    AuthCodeType,
    AuthVerifyType,
    send_verify_code,
    validate_verify_code,
)
from ...utils import gen_random_string


def test_send_sign_up_verify_code(test_client: TestClient):
    data: Dict = {}
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"

    data["account"] = "user@example.com"
    resp = test_client.post("/sign_up/code", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.OK, resp_data
    assert resp_data["code_type"] == AuthCodeType.EMAIL.value
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == AuthVerifyType.SIGNUP.value

    data["account"] = "13800000000"
    resp = test_client.post("/sign_up/code", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.OK, resp_data
    assert resp_data["code_type"] == AuthCodeType.SMS.value
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == AuthVerifyType.SIGNUP.value

    data["account"] = "invalid-account"
    resp = test_client.post("/sign_up/code", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "手机号码或邮箱格式有误"


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
    ],
)
def test_sign_up_with_verify_code_failed(
    test_client: TestClient, data: Dict, errors: Dict
):
    resp = test_client.post("/sign_up/verify", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"] == errors


async def test_validate_code(edgedb_client: edgedb.AsyncIOClient):
    account: str = "13800000000"

    rv = await validate_verify_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code="12345678",
    )
    assert not rv.code_found
    assert not rv.code_valid

    code: str = gen_random_string(6, letters=string.digits)
    await send_verify_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
        ttl=-1,
    )

    rv = await validate_verify_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
    )
    assert rv.code_found
    assert not rv.code_valid

    code: str = gen_random_string(6, letters=string.digits)
    await send_verify_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
        ttl=300,
    )

    rv = await validate_verify_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
    )
    assert rv.code_found
    assert rv.code_valid

    rv = await validate_verify_code(
        edgedb_client,
        account=account,
        code_type=AuthCodeType.SMS.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
    )
    assert not rv.code_found
    assert not rv.code_valid
