from __future__ import annotations

from http import HTTPStatus
from typing import Dict

from fastapi.testclient import TestClient

from ...queries.query_api import CodeType


def test_send_verify_code(test_client: TestClient):
    data: Dict = {}
    resp = test_client.post("/verify_codes", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["account"] == "该字段为必填项"
    assert error["detail"]["errors"]["code_type"] == "该字段为必填项"

    data: Dict = dict(
        account="user@example.com",
        code_type=CodeType.EMAIL.value,
    )
    resp = test_client.post("/verify_codes", json=data)
    assert resp.status_code == HTTPStatus.CREATED, resp.json()
