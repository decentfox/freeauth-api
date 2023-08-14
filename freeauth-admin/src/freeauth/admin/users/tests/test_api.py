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

import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from freeauth.db.admin.admin_qry_async_edgeql import (
    CreateDepartmentResult,
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    CreateRoleResult,
    CreateUserResult,
)


def create_user(
    bo_client: TestClient,
    name: str | None = None,
    username: str | None = None,
    email: str | None = None,
    mobile: str | None = None,
    password: str | None = None,
    organization_ids: list[str] | None = None,
    org_type_id: str | None = None,
) -> CreateUserResult:
    resp = bo_client.post(
        "/v1/users",
        json=dict(
            name=name,
            username=username,
            email=email,
            mobile=mobile,
            password=password,
            organization_ids=organization_ids,
            org_type_id=org_type_id,
        ),
    )
    user = resp.json()
    return CreateUserResult(**user)


@pytest.fixture
async def user(bo_client: TestClient) -> CreateUserResult:
    return create_user(
        bo_client,
        name="张三",
        username="user",
        email="user@example.com",
        mobile="13800000000",
    )


def test_create_user_at_least_one_field_error(bo_client: TestClient):
    data: Dict[str, str] = {}
    resp = bo_client.post("/v1/users", json=data)
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
            "用户名不能以数字开头，不得包含@符号，最大支持的长度为50个字符",
        ),
        (
            "username",
            "123abc",
            "用户名不能以数字开头，不得包含@符号，最大支持的长度为50个字符",
        ),
        (
            "username",
            "abc@test.com",
            "用户名不能以数字开头，不得包含@符号，最大支持的长度为50个字符",
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
    bo_client: TestClient, field: str, value: str, msg: str
):
    data: Dict[str, str] = {field: value}
    resp = bo_client.post("/v1/users", json=data)
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
    bo_client: TestClient, field: str, value: str
):
    data: Dict[str, str] = {field: value}
    resp = bo_client.post("/v1/users", json=data)
    assert resp.status_code == HTTPStatus.CREATED, resp.json()

    resp = bo_client.post("/v1/users", json=data)
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
    bo_client: TestClient, field: str, value: str, db_value: str
):
    data: Dict[str, str] = {field: value}
    if field == "name":
        data.update(username="user")
    resp = bo_client.post("/v1/users", json=data)
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
    bo_client: TestClient, field: str, value: str
):
    data: Dict[str, str] = dict(
        name="张三",
        username="user",
        mobile="13800000001",
        email="user@example.com",
    )
    data.update({field: value})
    resp = bo_client.post("/v1/users", json=data)
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user
    assert user[field] is None


@pytest.fixture
def org_type(bo_client: TestClient, faker) -> CreateOrgTypeResult:
    from ...organizations.tests.test_org_type_api import create_org_type

    return create_org_type(bo_client, faker)


@pytest.fixture
def enterprise(
    bo_client: TestClient, org_type: CreateOrgTypeResult, faker
) -> CreateEnterpriseResult:
    from ...organizations.tests.test_enterprise_api import create_enterprise

    return create_enterprise(bo_client, org_type, faker)


@pytest.fixture
def department(
    bo_client: TestClient, enterprise: CreateEnterpriseResult, faker
) -> CreateDepartmentResult:
    from ...organizations.tests.test_department_api import create_department

    return create_department(bo_client, enterprise, faker)


def test_create_user_with_organizations(
    bo_client: TestClient,
    org_type: CreateOrgTypeResult,
    enterprise: CreateEnterpriseResult,
    department: CreateDepartmentResult,
    faker,
):
    resp = bo_client.post(
        "/v1/users",
        json=dict(
            name=faker.name(),
            username=faker.user_name(),
            mobile=faker.phone_number(),
            email=faker.email(),
            organization_ids=[str(enterprise.id), str(department.id)],
            org_type_id=str(org_type.id),
        ),
    )
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user
    assert len(user["departments"]) == 2


def test_toggle_user_status(bo_client: TestClient, user: CreateUserResult):
    data: Dict = {}
    resp = bo_client.put("/v1/users/status", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data: Dict[str, Any] = {
        "user_ids": ["invalid_id"],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/users/status", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["user_ids.0"] == "ID格式错误"

    data: Dict = {
        "user_ids": ["12345678-1234-5678-1234-567812345678"],
        "is_deleted": False,
    }
    resp = bo_client.put("/v1/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == []

    data: Dict = {
        "user_ids": [str(user.id)],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == [
        {"id": str(user.id), "name": user.name, "is_deleted": True}
    ]

    data: Dict = {
        "user_ids": [str(user.id)],
        "is_deleted": False,
    }
    resp = bo_client.put("/v1/users/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == [
        {"id": str(user.id), "name": user.name, "is_deleted": False}
    ]


def test_delete_users(
    bo_client: TestClient,
    user: CreateUserResult,
    department: CreateDepartmentResult,
):
    data: Dict = {}
    resp = bo_client.request("DELETE", "/v1/users", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data: Dict = {
        "user_ids": ["invalid_id"],
    }
    resp = bo_client.request("DELETE", "/v1/users", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["user_ids.0"] == "ID格式错误"

    data: Dict = {
        "user_ids": ["12345678-1234-5678-1234-567812345678"],
    }
    resp = bo_client.request("DELETE", "/v1/users", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["users"] == []

    resp = bo_client.post("/v1/users", json={"username": "user1"})
    user1 = resp.json()
    resp = bo_client.post(
        "/v1/users",
        json={"username": "user2", "organization_ids": [str(department.id)]},
    )
    user2 = resp.json()

    data: Dict = {
        "user_ids": [str(user.id), user1["id"], user2["id"]],
    }
    resp = bo_client.request("DELETE", "/v1/users", json=data)
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
            "",
            "该字段不得为空",
        ),
        (
            "username",
            "long_username" * 4,
            "用户名不能以数字开头，不得包含@符号，最大支持的长度为50个字符",
        ),
        (
            "username",
            "123abc",
            "用户名不能以数字开头，不得包含@符号，最大支持的长度为50个字符",
        ),
        (
            "username",
            "abc@test.com",
            "用户名不能以数字开头，不得包含@符号，最大支持的长度为50个字符",
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
    bo_client: TestClient,
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
    resp = bo_client.put(f"/v1/users/{user.id}", json=data)
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
    bo_client: TestClient, user: CreateUserResult, field: str, value: str
):
    data: Dict[str, str] = {field: value}
    resp = bo_client.post("/v1/users", json=data)
    assert resp.status_code == HTTPStatus.CREATED, resp.json()

    data: Dict = dict(
        name=user.name,
        username=user.username,
        email=user.email,
        mobile=user.mobile,
    )
    data.update({field: value})
    resp = bo_client.put(f"/v1/users/{user.id}", json=data)
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
    bo_client: TestClient,
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
    resp = bo_client.put(f"/v1/users/{user.id}", json=data)
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert data[field] != updated_user[field] == db_value


def test_change_user_organizations(
    bo_client: TestClient,
    org_type: CreateOrgTypeResult,
    department: CreateDepartmentResult,
    faker,
):
    user = create_user(
        bo_client,
        name=faker.name(),
        username=faker.user_name(),
        mobile=faker.phone_number(),
        email=faker.email(),
        org_type_id=str(org_type.id),
    )
    resp = bo_client.put(f"/v1/users/{user.id}/organizations", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["organization_ids"] == "该字段为必填项"

    not_found_id = uuid.uuid4()
    ids = [str(department.id), str(uuid.uuid4())]
    resp = bo_client.put(
        f"/v1/users/{not_found_id}/organizations",
        json=dict(organization_ids=ids),
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "变更部门失败：用户不存在"

    resp = bo_client.put(
        f"/v1/users/{user.id}/organizations",
        json=dict(organization_ids=ids),
    )
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert len(updated_user["departments"]) == 1

    from ...organizations.tests.test_enterprise_api import create_enterprise
    from ...organizations.tests.test_org_type_api import create_org_type

    another_org_type = create_org_type(bo_client, faker)
    enterprise_1 = create_enterprise(bo_client, org_type, faker)
    enterprise_2 = create_enterprise(bo_client, another_org_type, faker)

    ids.extend([str(enterprise_1.id), str(enterprise_2.id)])
    resp = bo_client.put(
        f"/v1/users/{user.id}/organizations",
        json=dict(organization_ids=ids, org_type_id=str(another_org_type.id)),
    )
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert len(updated_user["departments"]) == 2
    for dept in updated_user["departments"]:
        assert dept["id"] in {str(department.id), str(enterprise_1.id)}
    assert updated_user["org_type"]["id"] == str(org_type.id)


def test_set_user_organizations(
    bo_client: TestClient,
    org_type: CreateOrgTypeResult,
    department: CreateDepartmentResult,
    faker,
):
    from ...organizations.tests.test_enterprise_api import create_enterprise
    from ...organizations.tests.test_org_type_api import create_org_type

    user = create_user(
        bo_client,
        name=faker.name(),
        username=faker.user_name(),
        mobile=faker.phone_number(),
        email=faker.email(),
    )
    another_org_type = create_org_type(bo_client, faker)
    enterprise = create_enterprise(bo_client, another_org_type, faker)

    ids = [str(department.id), str(uuid.uuid4()), str(enterprise.id)]
    resp = bo_client.put(
        f"/v1/users/{user.id}/organizations",
        json=dict(organization_ids=ids, org_type_id=None),
    )
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert len(updated_user["departments"]) == 0
    assert updated_user["org_type"] is None

    resp = bo_client.put(
        f"/v1/users/{user.id}/organizations",
        json=dict(organization_ids=ids, org_type_id=str(org_type.id)),
    )
    updated_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, updated_user
    assert len(updated_user["departments"]) == 1
    assert updated_user["departments"][0]["id"] == str(department.id)
    assert updated_user["org_type"]["id"] == str(org_type.id)


@pytest.fixture
def roles(bo_client: TestClient, org_type, faker) -> list[CreateRoleResult]:
    from ...roles.tests.test_api import create_role

    roles = [
        create_role(bo_client, faker, org_type_id=str(org_type.id)),
        create_role(bo_client, faker),
    ]
    return roles


def test_update_member_roles(
    bo_client: TestClient, roles, org_type, enterprise, department, faker
):
    user_1 = create_user(
        bo_client,
        name=faker.name(),
        username=faker.user_name(),
        mobile=faker.phone_number(),
        email=faker.email(),
    )
    resp = bo_client.put(
        f"/v1/users/{user_1.id}/roles",
        json=dict(role_ids=[str(r.id) for r in roles]),
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert not rv["departments"]
    assert len(rv["roles"]) == 1
    assert rv["roles"][0]["code"] == roles[1].code

    user_2 = create_user(
        bo_client,
        name=faker.name(),
        username=faker.user_name(),
        mobile=faker.phone_number(),
        email=faker.email(),
        organization_ids=[str(enterprise.id), str(department.id)],
        org_type_id=str(org_type.id),
    )
    resp = bo_client.put(
        f"/v1/users/{user_2.id}/roles",
        json=dict(role_ids=[str(r.id) for r in roles]),
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["departments"]) == 2
    assert len(rv["roles"]) == 2

    resp = bo_client.put(
        f"/v1/users/{user_2.id}/roles",
        json=dict(role_ids=[]),
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["departments"]) == 2
    assert len(rv["roles"]) == 0

    from ...organizations.tests.test_org_type_api import create_org_type

    another_org_type = create_org_type(bo_client, faker)
    user_3 = create_user(
        bo_client,
        name=faker.name(),
        username=faker.user_name(),
        mobile=faker.phone_number(),
        email=faker.email(),
        org_type_id=str(another_org_type.id),
    )
    resp = bo_client.put(
        f"/v1/users/{user_3.id}/roles",
        json=dict(role_ids=[str(r.id) for r in roles]),
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["departments"]) == 0
    assert len(rv["roles"]) == 1
    assert rv["roles"][0]["code"] == roles[1].code


def test_resign_user(
    bo_client: TestClient,
    org_type: CreateOrgTypeResult,
    enterprise: CreateEnterpriseResult,
    department: CreateDepartmentResult,
    roles,
    faker,
):
    users = []
    for _ in range(3):
        users.append(
            create_user(
                bo_client,
                name=faker.name(),
                username=faker.user_name(),
                mobile=faker.phone_number(),
                email=faker.email(),
                organization_ids=[str(enterprise.id), str(department.id)],
                org_type_id=str(org_type.id),
            )
        )

    resp = bo_client.post(
        "/v1/users/resign",
        json=dict(user_ids=[str(u.id) for u in users]),
    )
    resigned_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, resigned_user
    assert len(resigned_user) == 3

    for user in users:
        resp = bo_client.get(f"/v1/users/{user.id}")
        rv = resp.json()
        assert resp.status_code == HTTPStatus.OK, rv
        assert not rv["is_deleted"]
        assert not rv["roles"]
        assert not rv["departments"]


def test_resign_and_disable_user(
    bo_client: TestClient,
    enterprise: CreateEnterpriseResult,
    department: CreateDepartmentResult,
    faker,
):
    users = []
    for _ in range(3):
        users.append(
            create_user(
                bo_client,
                name=faker.name(),
                username=faker.user_name(),
                mobile=faker.phone_number(),
                email=faker.email(),
                organization_ids=[str(enterprise.id), str(department.id)],
            )
        )
    resp = bo_client.post(
        "/v1/users/resign",
        json=dict(user_ids=[str(u.id) for u in users], is_deleted=True),
    )
    resigned_user = resp.json()
    assert resp.status_code == HTTPStatus.OK, resigned_user
    assert len(resigned_user) == 3

    for user in users:
        resp = bo_client.get(f"/v1/users/{user.id}")
        rv = resp.json()
        assert resp.status_code == HTTPStatus.OK, rv
        assert rv["is_deleted"]
        assert not rv["roles"]
        assert not rv["departments"]


def test_get_user(bo_client: TestClient, user: CreateUserResult):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = bo_client.get(f"/v1/users/{not_found_id}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取用户信息失败：用户不存在"

    resp = bo_client.get(f"/v1/users/{user.id}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateUserResult(**resp.json()) == user


def test_query_users(bo_client: TestClient, bo_user, faker):
    from ...organizations.tests.test_org_type_api import create_org_type

    org_type_1 = create_org_type(bo_client, faker)
    org_type_2 = create_org_type(bo_client, faker)

    users: List[CreateUserResult] = [
        create_user(bo_client, name=faker.name(), username=faker.user_name())
    ]
    for _ in range(3):
        users.append(
            create_user(
                bo_client,
                name=faker.name(),
                username=faker.user_name(),
                mobile=faker.phone_number(),
                email=faker.email(),
            )
        )
    for _ in range(3):
        users.append(
            create_user(
                bo_client,
                name=faker.name(),
                username=faker.user_name(),
                email=faker.email(),
                org_type_id=str(org_type_1.id),
            )
        )
    for _ in range(3):
        users.append(
            create_user(
                bo_client,
                name=faker.name(),
                username=faker.user_name(),
                mobile=faker.phone_number(),
                org_type_id=str(org_type_2.id),
            )
        )

    status_data: Dict = {
        "user_ids": [],
        "is_deleted": True,
    }
    for idx in {3, 5, 7}:
        status_data["user_ids"].append(str(users[idx].id))
        users[idx].is_deleted = True
    bo_client.put("/v1/users/status", json=status_data)

    data: Dict = dict()
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 11
    assert len(rv["rows"]) == 11
    assert rv["page"] == 1
    assert rv["per_page"] == 20

    data["q"] = users[0].name
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["name"] == users[0].name

    data["q"] = "example.com"
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert all(data["q"] in u["email"] for u in rv["rows"])

    data = dict(
        page=1,
        per_page=3,
    )
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["last"] == 4
    assert len(rv["rows"]) == 3

    data["page"] = 4
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["page"] == 4
    assert len(rv["rows"]) == 2

    data = dict(
        order_by=["username"],
    )
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    username_list = [u.username or "" for u in users] + [bo_user.username]
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted(username_list) == [u["username"] for u in rv["rows"]]

    data["order_by"] = ["-username"]
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted(username_list, reverse=True) == [
        u["username"] for u in rv["rows"]
    ]

    data["order_by"] = ["-is_deleted", "username"]
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert [
        str(u.id)
        for u in sorted(users, key=lambda u: (-u.is_deleted, u.username or ""))
    ] == [u["id"] for u in rv["rows"] if u["id"] != str(bo_user.id)]

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
    resp = bo_client.post("/v1/users/query", json=data)
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
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["rows"]) == 7
    assert users[0].username not in [u["username"] for u in rv["rows"]]

    data = {"include_unassigned_users": False}
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 6
    assert all(u["org_type"] is not None for u in rv["rows"])

    data = {
        "include_unassigned_users": False,
        "org_type_id": str(org_type_1.id),
    }
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 3
    assert all(u["org_type"]["name"] == org_type_1.name for u in rv["rows"])

    data = {
        "org_type_id": str(org_type_2.id),
    }
    resp = bo_client.post("/v1/users/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 8
    assert all(
        u["org_type"] is None or u["org_type"]["name"] == org_type_2.name
        for u in rv["rows"]
    )
