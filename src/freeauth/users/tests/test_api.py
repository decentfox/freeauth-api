from __future__ import annotations

import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from ...query_api import (
    CreateDepartmentResult,
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    CreateUserResult,
)


def create_user(
    test_client: TestClient,
    name: str | None = None,
    username: str | None = None,
    email: str | None = None,
    mobile: str | None = None,
    organization_ids: list[int] | None = None,
) -> CreateUserResult:
    resp = test_client.post(
        "/v1/users",
        json=dict(
            name=name,
            username=username,
            email=email,
            mobile=mobile,
            organization_ids=organization_ids,
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
    )


def test_create_user_at_least_one_field_error(test_client: TestClient):
    data: Dict[str, str] = {}
    resp = test_client.post("/v1/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["__root__"]
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
    resp = test_client.post("/v1/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


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
    resp = test_client.post("/v1/users", json=data)
    assert resp.status_code == HTTPStatus.CREATED, resp.json()

    resp = test_client.post("/v1/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"][field] == f"{value} 已被使用"


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
    resp = test_client.post("/v1/users", json=data)
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user
    assert data[field] != user[field] == db_value


@pytest.mark.parametrize(
    "field,value",
    [
        ("mobile", ""),
        ("email", ""),
    ],
)
def test_create_user_empty_string(
    test_client: TestClient, field: str, value: str
):
    data: Dict[str, str] = dict(
        name="张三",
        username="user",
        mobile="13800000001",
        email="user@example.com",
    )
    data.update({field: value})
    resp = test_client.post("/v1/users", json=data)
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user
    assert user[field] is None


@pytest.fixture
def org_type(test_client: TestClient, faker) -> CreateOrgTypeResult:
    from ...organizations.tests.test_org_type_api import create_org_type

    return create_org_type(test_client, faker)


@pytest.fixture
def enterprise(
    test_client: TestClient, org_type: CreateOrgTypeResult, faker
) -> CreateEnterpriseResult:
    from ...organizations.tests.test_enterprise_api import create_enterprise

    return create_enterprise(test_client, org_type, faker)


@pytest.fixture
def department(
    test_client: TestClient, enterprise: CreateEnterpriseResult, faker
) -> CreateDepartmentResult:
    from ...organizations.tests.test_department_api import create_department

    return create_department(test_client, enterprise, faker)


def test_create_user_with_organizations(
    test_client: TestClient,
    enterprise: CreateEnterpriseResult,
    department: CreateDepartmentResult,
    faker,
):
    resp = test_client.post(
        "/v1/users",
        json=dict(
            name=faker.name(),
            username=faker.user_name(),
            mobile=faker.phone_number(),
            email=faker.email(),
            organization_ids=[str(enterprise.id), str(department.id)],
        ),
    )
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user
    assert len(user["departments"]) == 2


def test_toggle_user_status(test_client: TestClient, user: CreateUserResult):
    data: Dict = {}
    resp = test_client.put("/v1/users/status", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data: Dict[str, Any] = {
        "user_ids": ["invalid_id"],
        "is_deleted": True,
    }
    resp = test_client.put("/v1/users/status", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["user_ids.0"] == "ID格式错误"

    data: Dict = {
        "user_ids": ["12345678-1234-5678-1234-567812345678"],
        "is_deleted": False,
    }
    resp = test_client.put("/v1/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == []

    data: Dict = {
        "user_ids": [str(user.id)],
        "is_deleted": True,
    }
    resp = test_client.put("/v1/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == [
        {"id": str(user.id), "name": user.name, "is_deleted": True}
    ]

    data: Dict = {
        "user_ids": [str(user.id)],
        "is_deleted": False,
    }
    resp = test_client.put("/v1/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == [
        {"id": str(user.id), "name": user.name, "is_deleted": False}
    ]


def test_delete_users(test_client: TestClient, user: CreateUserResult):
    data: Dict = {}
    resp = test_client.request("DELETE", "/v1/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data: Dict = {
        "user_ids": ["invalid_id"],
    }
    resp = test_client.request("DELETE", "/v1/users", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["user_ids.0"] == "ID格式错误"

    data: Dict = {
        "user_ids": ["12345678-1234-5678-1234-567812345678"],
    }
    resp = test_client.request("DELETE", "/v1/users", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == []

    resp = test_client.post("/v1/users", json={"username": "user1"})
    user1 = resp.json()
    resp = test_client.post("/v1/users", json={"username": "user2"})
    user2 = resp.json()

    data: Dict = {
        "user_ids": [str(user.id), user1["id"], user2["id"]],
    }
    resp = test_client.request("DELETE", "/v1/users", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert sorted(u["id"] for u in resp.json()["users"]) == sorted(
        [str(user.id), user1["id"], user2["id"]]
    )


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
    resp = test_client.put(f"/v1/users/{user.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


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
    resp = test_client.post("/v1/users", json=data)
    assert resp.status_code == HTTPStatus.CREATED, resp.json()

    data: Dict = dict(
        name=user.name,
        username=user.username,
        email=user.email,
        mobile=user.mobile,
    )
    data.update({field: value})
    resp = test_client.put(f"/v1/users/{user.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"][field] == f"{value} 已被使用"


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
    resp = test_client.put(f"/v1/users/{user.id}", json=data)
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert data[field] != updated_user[field] == db_value


def test_update_user_with_organizations(
    test_client: TestClient,
    user: CreateUserResult,
    department: CreateDepartmentResult,
    faker,
):
    resp = test_client.put(
        f"/v1/users/{user.id}",
        json=dict(
            name=faker.name(),
            username=faker.user_name(),
            mobile=faker.phone_number(),
            email=faker.email(),
            organization_ids=[str(department.id), str(uuid.uuid4())],
        ),
    )
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert len(updated_user["departments"]) == 1


def test_get_user(test_client: TestClient, user: CreateUserResult):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = test_client.get(f"/v1/users/{not_found_id}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取用户信息失败：用户不存在"

    resp = test_client.get(f"/v1/users/{user.id}")
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
    test_client.put("/v1/users/status", json=status_data)

    data: Dict = dict()
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 10
    assert len(rv["rows"]) == 10
    assert rv["page"] == 1
    assert rv["per_page"] == 20

    data["q"] = users[0].name
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["name"] == users[0].name

    data["q"] = "example.com"
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert all(data["q"] in u["email"] for u in rv["rows"])

    data = dict(
        page=1,
        per_page=3,
    )
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["last"] == 4
    assert len(rv["rows"]) == 3

    data["page"] = 4
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["page"] == 4
    assert len(rv["rows"]) == 1

    data = dict(
        order_by=["username"],
    )
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted(u.username or "" for u in users) == [
        u["username"] for u in rv["rows"]
    ]

    data["order_by"] = ["-username"]
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted([u.username or "" for u in users], reverse=True) == [
        u["username"] for u in rv["rows"]
    ]

    data["order_by"] = ["-is_deleted", "username"]
    resp = test_client.post("/v1/users/query", json=data)
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
    resp = test_client.post("/v1/users/query", json=data)
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
    resp = test_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["rows"]) == 6
    assert users[0].username not in [u["username"] for u in rv["rows"]]
