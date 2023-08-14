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
from http import HTTPStatus
from typing import Any

import pytest
from fastapi.testclient import TestClient

from freeauth.db.admin.admin_qry_async_edgeql import (
    CreateOrgTypeResult,
    CreateRoleResult,
    CreateUserResult,
)


@pytest.fixture
def org_type(bo_client: TestClient, faker) -> CreateOrgTypeResult:
    from ...organizations.tests.test_org_type_api import create_org_type

    return create_org_type(bo_client, faker)


@pytest.mark.parametrize(
    "field,value,msg",
    [
        (
            "name",
            None,
            "该字段不得为空",
        ),
        (
            "name",
            "",
            "该字段为必填项",
        ),
        (
            "name",
            "   ",
            "该字段为必填项",
        ),
    ],
)
def test_create_role_validate_errors(
    bo_client: TestClient, field: str | None, value: str | None, msg: str
):
    data: dict[str, str | None] = {}
    if field:
        data = {field: value}
    resp = bo_client.post("/v1/roles", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


def test_create_role(bo_client: TestClient, faker, org_type):
    data: dict[str, Any] = {
        "name": faker.company_prefix() + "经理",
        "code": faker.lexify("?" * 10),
        "description": faker.sentence(),
        "org_type_id": None,
    }
    resp = bo_client.post("/v1/roles", json=data)
    role = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, role
    assert role["name"] == data["name"]
    assert role["code"] == data["code"].upper()
    assert not role["is_deleted"]
    assert not role["org_type"]

    data["code"] = faker.lexify("?" * 10)
    data["org_type_id"] = str(org_type.id)
    resp = bo_client.post("/v1/roles", json=data)
    role = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, role
    assert role["org_type"]["code"] == org_type.code
    assert role["org_type"]["name"] == org_type.name

    data["code"] = role["code"].upper()
    resp = bo_client.post("/v1/roles", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{data['code']} 已被使用"


def create_role(
    bo_client: TestClient, faker, org_type_id: str | None = None
) -> CreateRoleResult:
    resp = bo_client.post(
        "/v1/roles",
        json={
            "name": faker.company_prefix() + "经理",
            "code": faker.lexify("?" * 10),
            "description": faker.sentence(),
            "org_type_id": org_type_id,
        },
    )
    return CreateRoleResult(**resp.json())


@pytest.fixture
def role(bo_client: TestClient, faker) -> CreateRoleResult:
    return create_role(bo_client, faker)


def test_update_role(bo_client: TestClient, role: CreateRoleResult, faker):
    data: dict[str, Any] = {
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_deleted": role.is_deleted,
    }
    resp = bo_client.put(f"/v1/roles/{uuid.uuid4()}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "更新角色失败：角色不存在"

    resp = bo_client.put(f"/v1/roles/{role.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert CreateRoleResult(**rv) == role

    data = {
        "name": f"    {role.name}",
        "code": f"   {role.code}",
        "description": f"    {role.description}",
    }
    resp = bo_client.put(f"/v1/roles/{role.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert CreateRoleResult(**rv) == role

    data = {
        "name": "new name",
        "is_deleted": True,
    }
    resp = bo_client.put(f"/v1/roles/{role.code}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["name"] == "new name"
    assert not rv["code"]
    assert not rv["description"]
    assert rv["is_deleted"]

    another_role = create_role(bo_client, faker)
    data["code"] = (another_role.code or "").upper()
    resp = bo_client.put(f"/v1/roles/{role.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{data['code']} 已被使用"


def test_get_role(bo_client: TestClient, role: CreateRoleResult):
    resp = bo_client.get(f"/v1/roles/{uuid.uuid4()}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取角色信息失败：角色不存在"

    resp = bo_client.get(f"/v1/roles/{role.id}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateRoleResult(**resp.json()) == role

    resp = bo_client.get(f"/v1/roles/{role.code}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateRoleResult(**resp.json()) == role


def test_toggle_role_status(bo_client: TestClient, faker):
    data: dict[str, Any] = {}
    resp = bo_client.put("/v1/roles/status", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data = {
        "ids": ["invalid_id"],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/roles/status", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "ID格式错误"

    data = {
        "ids": [str(uuid.uuid4())],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/roles/status", json=data)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == []

    role_1 = create_role(bo_client, faker)
    role_2 = create_role(bo_client, faker)
    data = {
        "ids": [str(role_1.id)],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/roles/status", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 1
    assert rv[0]["is_deleted"]

    data = {
        "ids": [str(role_1.id), str(role_2.id)],
        "is_deleted": False,
    }
    resp = bo_client.put("/v1/roles/status", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 2
    assert not rv[0]["is_deleted"]
    assert not rv[1]["is_deleted"]


def test_delete_roles(bo_client: TestClient, faker):
    data: dict[str, Any] = {}
    resp = bo_client.request("DELETE", "/v1/roles", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data = {"ids": ["invalid_id"]}
    resp = bo_client.request("DELETE", "/v1/roles", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "ID格式错误"

    data = {"ids": [str(uuid.uuid4())]}
    resp = bo_client.request("DELETE", "/v1/roles", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 0

    role_1 = create_role(bo_client, faker)
    role_2 = create_role(bo_client, faker)

    ids = [str(role_1.id), str(role_2.id)]
    data = {"ids": ids}
    resp = bo_client.request("DELETE", "/v1/roles", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 2
    assert sorted(role["id"] for role in rv) == sorted(ids)


@pytest.fixture
def org_types(bo_client: TestClient, faker):
    from ...organizations.tests.test_org_type_api import create_org_type

    org_types = []
    for _ in range(3):
        org_types.append(create_org_type(bo_client, faker))
    return org_types


@pytest.fixture
def roles(bo_client: TestClient, org_types, faker):
    roles = []
    for _ in range(2):
        roles.append(create_role(bo_client, faker))
    for _ in range(2):
        roles.append(
            create_role(bo_client, faker, org_type_id=str(org_types[0].id))
        )
    for _ in range(2):
        roles.append(
            create_role(bo_client, faker, org_type_id=str(org_types[1].id))
        )
    for _ in range(2):
        roles.append(
            create_role(bo_client, faker, org_type_id=str(org_types[2].id))
        )
    return roles


def test_get_roles(bo_client: TestClient, roles, org_types):
    data: dict[str, Any] = dict(
        per_page=3,
    )
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 8
    assert len(rv["rows"]) == 3
    assert rv["page"] == 1
    assert rv["per_page"] == 3

    data["q"] = roles[0].name
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["name"] == roles[0].name

    data["q"] = org_types[0].name
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2
    assert rv["rows"][0]["org_type"]["name"] == org_types[0].name
    assert rv["rows"][1]["org_type"]["name"] == org_types[0].name

    data = {"include_global_roles": False}
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 6
    for ot in rv["rows"]:
        assert ot["org_type"] is not None

    data = {
        "include_global_roles": False,
        "org_type_id": str(org_types[2].id),
    }
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2
    assert rv["rows"][0]["org_type"]["name"] == org_types[2].name
    assert rv["rows"][1]["org_type"]["name"] == org_types[2].name

    data = {
        "org_type_id": str(org_types[0].id),
    }
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 4
    for ot in rv["rows"]:
        assert (
            ot["org_type"] is None
            or ot["org_type"]["name"] == org_types[0].name
        )

    data = {"include_org_type_roles": False}
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2
    for ot in rv["rows"]:
        assert ot["org_type"] is None

    data = {
        "include_org_type_roles": False,
        "include_global_roles": False,
    }
    resp = bo_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 0


def test_bind_or_unbind_users_to_roles(
    bo_client: TestClient, roles, org_types, faker
):
    from ...users.tests.test_api import create_user

    resp = bo_client.post("/v1/roles/bind_users", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["user_ids"] == "该字段为必填项"
    assert error["detail"]["errors"]["role_ids"] == "该字段为必填项"

    resp = bo_client.post(
        "/v1/roles/bind_users",
        json={
            "user_ids": [],
            "role_ids": [],
        },
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["user_ids"] == "请至少选择一项"
    assert error["detail"]["errors"]["role_ids"] == "请至少选择一项"

    users: list[CreateUserResult] = [
        create_user(bo_client, name=faker.name(), username=faker.user_name()),
        create_user(
            bo_client,
            name=faker.name(),
            username=faker.user_name(),
            org_type_id=str(org_types[0].id),
        ),
        create_user(
            bo_client,
            name=faker.name(),
            username=faker.user_name(),
            org_type_id=str(org_types[1].id),
        ),
    ]
    resp = bo_client.post(
        "/v1/roles/bind_users",
        json={
            "user_ids": [str(u.id) for u in users],
            "role_ids": [str(r.id) for r in roles],
        },
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    for user in rv:
        if user["id"] == str(users[0].id):
            assert len(user["roles"]) == 2  # global roles
            assert sorted(r["id"] for r in user["roles"]) == sorted(
                str(r.id) for r in roles[0:2]
            )
        else:
            assert len(user["roles"]) == 4  # global + org_type roles

            if user["id"] == str(users[1].id):
                assert sorted(r["id"] for r in user["roles"]) == sorted(
                    str(r.id) for r in roles[0:4]
                )
            else:
                assert sorted(r["id"] for r in user["roles"]) == sorted(
                    str(r.id) for r in (roles[0:2] + roles[4:6])
                )

    resp = bo_client.post("/v1/roles/unbind_users", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["user_ids"] == "该字段为必填项"
    assert error["detail"]["errors"]["role_ids"] == "该字段为必填项"

    resp = bo_client.post(
        "/v1/roles/unbind_users",
        json={
            "user_ids": [],
            "role_ids": [],
        },
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["user_ids"] == "请至少选择一项"
    assert error["detail"]["errors"]["role_ids"] == "请至少选择一项"

    resp = bo_client.post(
        "/v1/roles/unbind_users",
        json={
            "user_ids": [str(u.id) for u in users],
            "role_ids": [str(r.id) for r in roles[7:]],
        },
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    for user in rv:
        if user["id"] == str(users[0].id):
            assert len(user["roles"]) == 2  # global roles
        else:
            assert len(user["roles"]) == 4  # global + org_type roles

    resp = bo_client.post(
        "/v1/roles/unbind_users",
        json={
            "user_ids": [str(u.id) for u in users],
            "role_ids": [str(r.id) for r in roles[0:2]],
        },
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    for user in rv:
        if user["id"] == str(users[0].id):
            assert len(user["roles"]) == 0  # global roles removed
        else:
            assert len(user["roles"]) == 2  # org_type roles left

    resp = bo_client.post(
        "/v1/roles/unbind_users",
        json={
            "user_ids": [str(u.id) for u in users],
            "role_ids": [str(r.id) for r in roles],
        },
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    for user in rv:
        assert not user["roles"]
