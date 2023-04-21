from __future__ import annotations

from http import HTTPStatus
from typing import Dict

from fastapi.testclient import TestClient

from ...queries.query_api import AuthCodeType, AuthVerifyType


def test_send_verify_code(test_client: TestClient):
    data: Dict = {}
    resp = test_client.post("/verify_codes", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"
    assert error["detail"]["errors"]["verify_type"] == "该字段为必填项"

    data: Dict = dict(
        account="user@example.com",
        verify_type=AuthVerifyType.LOGIN.value,
    )
    resp = test_client.post("/verify_codes", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, resp_data
    assert resp_data["code_type"] == AuthCodeType.EMAIL.value
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == AuthVerifyType.LOGIN.value

    data: Dict = dict(
        account="13800000000",
        verify_type=AuthVerifyType.REGISTER.value,
    )
    resp = test_client.post("/verify_codes", json=data)
    resp_data = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, resp_data
    assert resp_data["code_type"] == AuthCodeType.SMS.value
    assert resp_data["account"] == data["account"]
    assert resp_data["verify_type"] == AuthVerifyType.REGISTER.value

    data["verify_type"] = "invalid-type"
    resp = test_client.post("/verify_codes", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["verify_type"] == "不是有效的枚举值"

    data["account"] = "invalid-account"
    resp = test_client.post("/verify_codes", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "手机号码或邮箱格式有误"
