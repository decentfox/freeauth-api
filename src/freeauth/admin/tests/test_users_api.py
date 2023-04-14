from __future__ import annotations

from http import HTTPStatus
from typing import Dict

import pytest
from fastapi.testclient import TestClient


def test_create_user_at_least_one_field_error(test_client: TestClient):
    data: Dict[str, str] = {}
    resp = test_client.post("/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"][0]["msg"]
        == "用户名、邮箱、手机号三个信息中请至少提供一项"
    )


@pytest.mark.parametrize(
    "field,value,msg",
    [
        (
            "username",
            "long_username" * 4,
            "最大支持的长度为50个字符",
        ),
        (
            "name",
            "很长的名字" * 11,
            "最大支持的长度为50个字符",
        ),
        (
            "email",
            "invalid email address",
            "邮箱格式有误",
        ),
        (
            "mobile",
            "invalid mobile",
            "仅支持中国大陆11位手机号",
        ),
    ],
)
def test_create_user_validate_errors(
    test_client: TestClient, field: str, value: str, msg: str
):
    data: Dict[str, str] = {field: value}
    resp = test_client.post("/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"][0]["msg"] == msg


@pytest.mark.parametrize(
    "field,value",
    [
        ("username", "user1"),
        ("mobile", "13800000001"),
        ("email", "user1@example.com"),
    ],
)
def test_create_user_exist_error(
    test_client: TestClient, field: str, value: str
):
    data: Dict[str, str] = {field: value}
    resp = test_client.post("/users", json=data)
    assert resp.status_code == HTTPStatus.CREATED, resp.json()

    resp = test_client.post("/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["error"] == f'"{value}" 已被使用'


@pytest.mark.parametrize(
    "field,value,db_value",
    [
        ("name", "  张三   ", "张三"),
        ("username", "  user  ", "user"),
        ("email", "  user@example.com   ", "user@example.com"),
        ("mobile", "  13800000001   ", "13800000001"),
    ],
)
def test_create_user_strip_whitespace(
    test_client: TestClient, field: str, value: str, db_value: str
):
    data: Dict[str, str] = {field: value}
    if field == "name":
        data.update(username="user")
    resp = test_client.post("/users", json=data)
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user
    assert data[field] != user[field] == db_value


def test_toggle_user_status(test_client: TestClient):
    data: Dict = {}
    resp = test_client.put("/users/status", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for item in error["detail"]:
        assert item["msg"] == "该字段为必填项"

    data: Dict = {
        "user_ids": ["invalid_id"],
        "is_deleted": True,
    }
    resp = test_client.put("/users/status", json=data)
    error = resp.json()
    assert error["detail"][0]["msg"] == "用户ID格式错误"

    data: Dict = {"username": "user1"}
    resp = test_client.post("/users", json=data)
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user

    data: Dict = {
        "user_ids": ["12345678-1234-5678-1234-567812345678"],
        "is_deleted": False,
    }
    resp = test_client.put("/users/status", json=data)
    assert resp.status_code == HTTPStatus.NOT_FOUND, resp.json()
    assert resp.json()["detail"]["error"] == "用户不存在"

    data: Dict = {
        "user_ids": [user["id"]],
        "is_deleted": True,
    }
    resp = test_client.put("/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["updated_ids"] == data["user_ids"]

    data: Dict = {
        "user_ids": [user["id"]],
        "is_deleted": False,
    }
    resp = test_client.put("/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["updated_ids"] == data["user_ids"]
