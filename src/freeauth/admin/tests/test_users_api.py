from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from ...queries.query_api import CreateUserResult


def create_user(
    test_client: TestClient,
    name: str | None = None,
    username: str | None = None,
    email: str | None = None,
    mobile: str | None = None,
    password: str | None = None,
) -> CreateUserResult:
    resp = test_client.post(
        "/users",
        json=dict(
            name=name,
            username=username,
            email=email,
            mobile=mobile,
            hashed_password=password,
        ),
    )
    user = resp.json()
    return CreateUserResult(**user)


@pytest.fixture
async def user(test_client: TestClient) -> CreateUserResult:
    return create_user(
        test_client,
        name="张三",
        username="user",
        email="user@example.com",
        mobile="13800000000",
        password="password",
    )


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
    assert error["detail"][0]["msg"] == f'"{value}" 已被使用'


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


def test_toggle_user_status(test_client: TestClient, user: CreateUserResult):
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

    data: Dict = {
        "user_ids": ["12345678-1234-5678-1234-567812345678"],
        "is_deleted": False,
    }
    resp = test_client.put("/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == []

    data: Dict = {
        "user_ids": [str(user.id)],
        "is_deleted": True,
    }
    resp = test_client.put("/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == [
        {"id": str(user.id), "name": user.name, "is_deleted": True}
    ]

    data: Dict = {
        "user_ids": [str(user.id)],
        "is_deleted": False,
    }
    resp = test_client.put("/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == [
        {"id": str(user.id), "name": user.name, "is_deleted": False}
    ]


def test_delete_users(test_client: TestClient, user: CreateUserResult):
    data: Dict = {}
    resp = test_client.request("DELETE", "/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for item in error["detail"]:
        assert item["msg"] == "该字段为必填项"

    data: Dict = {
        "user_ids": ["invalid_id"],
    }
    resp = test_client.request("DELETE", "/users", json=data)
    error = resp.json()
    assert error["detail"][0]["msg"] == "用户ID格式错误"

    data: Dict = {
        "user_ids": ["12345678-1234-5678-1234-567812345678"],
    }
    resp = test_client.request("DELETE", "/users", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == []

    resp = test_client.post("/users", json={"username": "user1"})
    user1 = resp.json()
    resp = test_client.post("/users", json={"username": "user2"})
    user2 = resp.json()

    data: Dict = {
        "user_ids": [str(user.id), user1["id"], user2["id"]],
    }
    resp = test_client.request("DELETE", "/users", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == [
        {"id": str(user.id), "name": user.name},
        {"id": user1["id"], "name": user1["name"]},
        {"id": user2["id"], "name": user2["name"]},
    ]


@pytest.mark.parametrize(
    "field,value,msg",
    [
        (
            "name",
            None,
            "该字段不得为空",
        ),
        (
            "username",
            None,
            "该字段不得为空",
        ),
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
def test_update_user_validate_errors(
    test_client: TestClient,
    user: CreateUserResult,
    field: str,
    value: str,
    msg: str,
):
    data: Dict = dict(
        name="张三",
        username="user",
        email="user@example.com",
        mobile="13800000000",
    )
    data.update({field: value})
    resp = test_client.put(f"/users/{user.id}", json=data)
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
def test_update_user_exist_error(
    test_client: TestClient, user: CreateUserResult, field: str, value: str
):
    data: Dict[str, str] = {field: value}
    resp = test_client.post("/users", json=data)
    assert resp.status_code == HTTPStatus.CREATED, resp.json()

    data: Dict = dict(
        name=user.name,
        username=user.username,
        email=user.email,
        mobile=user.mobile,
    )
    data.update({field: value})
    resp = test_client.put(f"/users/{user.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"][0]["msg"] == f'"{value}" 已被使用'


@pytest.mark.parametrize(
    "field,value,db_value",
    [
        ("name", "  张三   ", "张三"),
        ("username", "  user1  ", "user1"),
        ("email", "  user1@example.com   ", "user1@example.com"),
        ("mobile", "  13800000001   ", "13800000001"),
    ],
)
def test_update_user_strip_whitespace(
    test_client: TestClient,
    user: CreateUserResult,
    field: str,
    value: str,
    db_value: str,
):
    data: Dict = dict(
        name=user.name,
        username=user.username,
        email=user.email,
        mobile=user.mobile,
    )
    data.update({field: value})
    resp = test_client.put(f"/users/{user.id}", json=data)
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert data[field] != updated_user[field] == db_value


def test_get_user(test_client: TestClient, user: CreateUserResult):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = test_client.get(f"/users/{not_found_id}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"] == "用户不存在"

    resp = test_client.get(f"/users/{user.id}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateUserResult(**resp.json()) == user


def test_query_users(test_client: TestClient, faker):
    users: List[CreateUserResult] = [
        create_user(test_client, name=faker.name(), username=faker.user_name())
    ]
    for _ in range(3):
        users.append(
            create_user(
                test_client,
                name=faker.name(),
                username=faker.user_name(),
                mobile=faker.phone_number(),
                email=faker.email(),
            )
        )
    for _ in range(3):
        users.append(
            create_user(
                test_client,
                name=faker.name(),
                username=faker.user_name(),
                email=faker.email(),
            )
        )
    for _ in range(3):
        users.append(
            create_user(
                test_client,
                name=faker.name(),
                username=faker.user_name(),
                mobile=faker.phone_number(),
            )
        )

    status_data: Dict = {
        "user_ids": [],
        "is_deleted": True,
    }
    for idx in {3, 5, 7}:
        status_data["user_ids"].append(str(users[idx].id))
        users[idx].is_deleted = True
    test_client.put("/users/status", json=status_data)

    data: Dict = dict()
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 10
    assert len(rv["rows"]) == 10
    assert rv["page"] == 1
    assert rv["per_page"] == 20

    data["q"] = users[0].name
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["name"] == users[0].name

    data["q"] = "example.com"
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert all(data["q"] in u["email"] for u in rv["rows"])

    data = dict(
        page=1,
        per_page=3,
    )
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["last"] == 4
    assert len(rv["rows"]) == 3

    data["page"] = 4
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["page"] == 4
    assert len(rv["rows"]) == 1

    data = dict(
        order_by=["username"],
    )
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted(u.username or "" for u in users) == [
        u["username"] for u in rv["rows"]
    ]

    data["order_by"] = ["-username"]
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted([u.username or "" for u in users], reverse=True) == [
        u["username"] for u in rv["rows"]
    ]

    data["order_by"] = ["-is_deleted", "username"]
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert [
        str(u.id)
        for u in sorted(users, key=lambda u: (-u.is_deleted, u.username or ""))
    ] == [u["id"] for u in rv["rows"]]

    data = dict(
        filter_by=[
            dict(field="username", operator="eq", value=users[0].username),
            dict(
                field="is_deleted",
                operator="neq",
                value=True,
            ),
            dict(
                field="created_at",
                operator="lte",
                value=datetime.utcnow()
                .replace(tzinfo=timezone.utc)
                .isoformat(),
            ),
        ],
    )
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["rows"]) == 1
    assert users[0].username == rv["rows"][0]["username"]

    data["filter_by"] = [
        dict(field="username", operator="neq", value=users[0].username),
        dict(
            field="is_deleted",
            operator="neq",
            value=True,
        ),
    ]
    resp = test_client.post("/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["rows"]) == 6
    assert users[0].username not in [u["username"] for u in rv["rows"]]
