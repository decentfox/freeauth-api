from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ...query_api import (
    CreateDepartmentResult,
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    CreateRoleResult,
)


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
    test_client: TestClient, field: str | None, value: str | None, msg: str
):
    data: dict[str, str | None] = {}
    if field:
        data = {field: value}
    resp = test_client.post("/v1/roles", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


def test_create_role(
    test_client: TestClient, faker, org_type, enterprise, department
):
    data: dict[str, Any] = {
        "name": faker.company_prefix() + "经理",
        "code": faker.lexify("?" * 10),
        "description": faker.sentence(),
        "organization_ids": [
            str(org_type.id),
            str(enterprise.id),
            str(department.id),
        ],
    }
    resp = test_client.post("/v1/roles", json=data)
    role = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, role
    assert role["name"] == data["name"]
    assert role["code"] == data["code"]
    assert not role["is_deleted"]
    assert len(role["organizations"]) == 3

    data["code"] = role["code"].upper()
    resp = test_client.post("/v1/roles", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{data['code']} 已被使用"


def create_role(
    test_client: TestClient, faker, organization_ids: list[str] | None = None
) -> CreateRoleResult:
    resp = test_client.post(
        "/v1/roles",
        json={
            "name": faker.company_prefix() + "经理",
            "code": faker.lexify("?" * 10),
            "description": faker.sentence(),
            "organization_ids": organization_ids,
        },
    )
    return CreateRoleResult(**resp.json())


@pytest.fixture
def role(test_client: TestClient, faker) -> CreateRoleResult:
    return create_role(test_client, faker)


def test_update_role(
    test_client: TestClient, role: CreateRoleResult, faker, department
):
    data: dict[str, Any] = {
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "organization_ids": [str(o.id) for o in role.organizations],
        "is_deleted": role.is_deleted,
    }
    resp = test_client.put(f"/v1/roles/{uuid.uuid4()}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "更新角色失败：角色不存在"

    resp = test_client.put(f"/v1/roles/{role.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert CreateRoleResult(**rv) == role

    data = {
        "name": f"    {role.name}",
        "code": f"   {role.code}",
        "description": f"    {role.description}",
        "organization_ids": [str(o.id) for o in role.organizations] + [
            str(uuid.uuid4())
        ],
    }
    resp = test_client.put(f"/v1/roles/{role.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert CreateRoleResult(**rv) == role

    data = {
        "name": "new name",
        "is_deleted": True,
        "organization_ids": [str(department.id)],
    }
    resp = test_client.put(f"/v1/roles/{role.code}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["name"] == "new name"
    assert not rv["code"]
    assert not rv["description"]
    assert rv["organizations"] == [
        {
            "id": str(department.id),
            "code": department.code,
            "name": department.name,
            "is_org_type": False,
            "is_department": True,
            "is_enterprise": False,
        }
    ]
    assert rv["is_deleted"]

    another_role = create_role(test_client, faker)
    data["code"] = (another_role.code or "").upper()
    resp = test_client.put(f"/v1/roles/{role.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{data['code']} 已被使用"


def test_get_role(test_client: TestClient, role: CreateRoleResult):
    resp = test_client.get(f"/v1/roles/{uuid.uuid4()}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取角色信息失败：角色不存在"

    resp = test_client.get(f"/v1/roles/{role.id}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateRoleResult(**resp.json()) == role

    resp = test_client.get(f"/v1/roles/{role.code}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateRoleResult(**resp.json()) == role


def test_toggle_role_status(test_client: TestClient, faker):
    data: dict[str, Any] = {}
    resp = test_client.put("/v1/roles/status", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data = {
        "ids": ["invalid_id"],
        "is_deleted": True,
    }
    resp = test_client.put("/v1/roles/status", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "ID格式错误"

    data = {
        "ids": [str(uuid.uuid4())],
        "is_deleted": True,
    }
    resp = test_client.put("/v1/roles/status", json=data)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == []

    role_1 = create_role(test_client, faker)
    role_2 = create_role(test_client, faker)
    data = {
        "ids": [str(role_1.id)],
        "is_deleted": True,
    }
    resp = test_client.put("/v1/roles/status", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 1
    assert rv[0]["is_deleted"]

    data = {
        "ids": [str(role_1.id), str(role_2.id)],
        "is_deleted": False,
    }
    resp = test_client.put("/v1/roles/status", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 2
    assert not rv[0]["is_deleted"]
    assert not rv[1]["is_deleted"]


def test_delete_roles(test_client: TestClient, faker):
    data: dict[str, Any] = {}
    resp = test_client.request("DELETE", "/v1/roles", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data = {"ids": ["invalid_id"]}
    resp = test_client.request("DELETE", "/v1/roles", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "ID格式错误"

    data = {"ids": [str(uuid.uuid4())]}
    resp = test_client.request("DELETE", "/v1/roles", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 0

    role_1 = create_role(test_client, faker)
    role_2 = create_role(test_client, faker)

    ids = [str(role_1.id), str(role_2.id)]
    data = {"ids": ids}
    resp = test_client.request("DELETE", "/v1/roles", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 2
    assert sorted(role["id"] for role in rv) == sorted(ids)


def test_get_roles(
    test_client: TestClient, org_type, enterprise, department, faker
):
    roles = []
    for _ in range(2):
        roles.append(create_role(test_client, faker))
    for _ in range(2):
        roles.append(
            create_role(
                test_client, faker, organization_ids=[str(org_type.id)]
            )
        )
    for _ in range(2):
        roles.append(
            create_role(
                test_client, faker, organization_ids=[str(enterprise.id)]
            )
        )
    for _ in range(2):
        roles.append(
            create_role(
                test_client, faker, organization_ids=[str(department.id)]
            )
        )

    data: dict[str, Any] = dict(
        per_page=3,
    )
    resp = test_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 8
    assert len(rv["rows"]) == 3
    assert rv["page"] == 1
    assert rv["per_page"] == 3

    data["q"] = roles[0].name
    resp = test_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["name"] == roles[0].name

    data["q"] = org_type.name
    resp = test_client.post("/v1/roles/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2
    assert rv["rows"][0]["organizations"][0]["name"] == org_type.name
    assert rv["rows"][1]["organizations"][0]["name"] == org_type.name
