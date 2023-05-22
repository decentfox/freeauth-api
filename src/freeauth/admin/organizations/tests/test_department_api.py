from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from ...query_api import (
    CreateDepartmentResult,
    CreateDepartmentResultEnterprise,
    CreateDepartmentResultParent,
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    CreateUserResult,
)
from .test_enterprise_api import create_enterprise
from .test_org_type_api import create_org_type


@pytest.mark.parametrize(
    "field,value,msg",
    [
        (
            "parent_id",
            None,
            "该字段不得为空",
        ),
        (
            "parent_id",
            "",
            "ID格式错误",
        ),
        (
            "name",
            None,
            "该字段不得为空",
        ),
        (
            "name",
            "   ",
            "该字段为必填项",
        ),
    ],
)
def test_create_department_validate_errors(
    test_client: TestClient, field: str | None, value: str | None, msg: str
):
    data: dict[str, str | None] = {}
    if field:
        data = {field: value}
    resp = test_client.post("/v1/departments", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


@pytest.fixture
def org_type(test_client: TestClient, faker) -> CreateOrgTypeResult:
    return create_org_type(test_client, faker)


@pytest.fixture
def enterprise(
    test_client: TestClient, org_type: CreateOrgTypeResult, faker
) -> CreateEnterpriseResult:
    return create_enterprise(test_client, org_type, faker)


def test_create_department(
    test_client: TestClient, org_type: CreateOrgTypeResult, enterprise, faker
):
    data: dict[str, str] = {
        "parent_id": "12345678-1234-5678-1234-567812345678",
        "name": faker.company_prefix(),
        "code": faker.hexify("^" * 6),
        "description": faker.sentence(),
    }
    resp = test_client.post("/v1/departments", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert (
        error["detail"]["message"]
        == "创建部门分支失败：上级部门或企业机构不存在"
    )

    data["parent_id"] = str(enterprise.id)
    resp = test_client.post("/v1/departments", json=data)
    dept_1 = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, dept_1
    assert dept_1["name"] == data["name"]
    assert dept_1["enterprise"]["code"] == enterprise.code
    assert dept_1["parent"]["code"] == enterprise.code

    data.update(
        {
            "parent_id": dept_1["id"],
            "name": faker.company_prefix(),
            "code": faker.hexify("^" * 6),
            "description": faker.sentence(),
        }
    )
    resp = test_client.post("/v1/departments", json=data)
    dept_1_1 = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, dept_1_1
    assert dept_1_1["code"] == data["code"].upper()
    assert dept_1_1["name"] == data["name"]
    assert dept_1_1["enterprise"]["code"] == enterprise.code
    assert dept_1_1["parent"]["code"] == dept_1["code"]

    # same department code for different enterprise
    new_enterprise: CreateEnterpriseResult = create_enterprise(
        test_client, org_type, faker
    )
    data["parent_id"] = str(new_enterprise.id)
    resp = test_client.post("/v1/departments", json=data)
    dept_2 = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, dept_2
    assert dept_2["code"] == dept_1_1["code"]
    assert dept_2["enterprise"]["code"] == new_enterprise.code
    assert dept_2["parent"]["code"] == new_enterprise.code

    data["parent_id"] = str(enterprise.id)
    resp = test_client.post("/v1/departments", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{dept_1_1['code']} 已被使用"


def create_department(
    test_client: TestClient,
    parent: CreateEnterpriseResult | CreateDepartmentResult,
    faker,
) -> CreateDepartmentResult:
    data: dict[str, str] = {
        "parent_id": str(parent.id),
        "name": faker.company_prefix(),
        "code": faker.hexify("^" * 6, upper=True),
        "description": faker.sentence(),
    }
    resp = test_client.post("/v1/departments", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, rv
    rv.update(
        dict(
            enterprise=CreateDepartmentResultEnterprise(**rv["enterprise"]),
            parent=CreateDepartmentResultParent(**rv["parent"]),
        )
    )
    return CreateDepartmentResult(**rv)


@pytest.fixture
def department(
    test_client: TestClient, enterprise: CreateEnterpriseResult, faker
) -> CreateDepartmentResult:
    return create_department(test_client, enterprise, faker)


def test_update_department(
    test_client: TestClient,
    org_type: CreateOrgTypeResult,
    enterprise: CreateEnterpriseResult,
    department: CreateDepartmentResult,
    faker,
):
    # validating error
    data: dict[str, str] = {}
    resp = test_client.put(f"/v1/departments/{department.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["name"] == "该字段为必填项"
    assert error["detail"]["errors"]["parent_id"] == "该字段为必填项"

    # update by ID
    data = {
        "name": faker.company_prefix(),
        "code": faker.hexify("^" * 6, upper=True),
        "parent_id": str(department.parent.id),
    }
    resp = test_client.put(f"/v1/departments/{department.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["code"] == data["code"]
    old_code, department.code = department.code, rv["code"]

    # old code not found
    resp = test_client.put(f"/v1/departments/{old_code}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["message"] == "更新部门分支失败：缺少企业机构 ID"

    resp = test_client.put(
        f"/v1/departments/{old_code}",
        params={"enterprise_id": str(enterprise.id)},
        json=data,
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "更新部门分支失败：部门不存在"

    # update by code
    data["code"] = faker.hexify("^" * 6, upper=True)
    resp = test_client.put(
        f"/v1/departments/{department.code}",
        params={"enterprise_id": str(enterprise.id)},
        json=data,
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["id"] == str(department.id)
    assert rv["code"] == data["code"]
    old_code, department.code = department.code, rv["code"]

    resp = test_client.put(
        f"/v1/departments/{department.code}",
        params={"enterprise_id": str(enterprise.id)},
        json=data,
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv

    # same department code for different enterprise
    new_enterprise = create_enterprise(test_client, org_type, faker)
    dept_1 = create_department(test_client, new_enterprise, faker)
    dept_2 = create_department(test_client, enterprise, faker)

    data = {
        "name": department.name,
        "code": dept_1.code,
        "parent_id": str(enterprise.id),
    }
    resp = test_client.put(f"/v1/departments/{department.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["code"] == dept_1.code

    data = {
        "name": department.name,
        "code": dept_2.code,
        "parent_id": str(enterprise.id),
    }
    resp = test_client.put(f"/v1/departments/{department.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{dept_2.code} 已被使用"


def test_get_department(
    test_client: TestClient,
    enterprise: CreateEnterpriseResult,
    department: CreateDepartmentResult,
):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = test_client.get(f"/v1/departments/{not_found_id}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取部门分支信息失败：部门不存在"

    resp = test_client.get(f"/v1/departments/{department.id}")
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    rv.update(
        dict(
            enterprise=CreateDepartmentResultEnterprise(**rv["enterprise"]),
            parent=CreateDepartmentResultParent(**rv["parent"]),
        )
    )
    assert CreateDepartmentResult(**rv) == department

    resp = test_client.get(f"/v1/departments/{department.code}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert (
        error["detail"]["message"] == "获取部门分支信息失败：缺少企业机构 ID"
    )

    resp = test_client.get(
        f"/v1/departments/{department.code}",
        params={"enterprise_id": str(enterprise.id)},
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    rv.update(
        dict(
            enterprise=CreateDepartmentResultEnterprise(**rv["enterprise"]),
            parent=CreateDepartmentResultParent(**rv["parent"]),
        )
    )
    assert CreateDepartmentResult(**rv) == department


def test_get_organization_tree_by_org_type(
    test_client: TestClient, org_type: CreateOrgTypeResult, faker
):
    enterprise_1 = create_enterprise(test_client, org_type, faker)
    enterprise_2 = create_enterprise(test_client, org_type, faker)

    dept_in_e1 = []
    for i in range(2):
        dept = create_department(test_client, enterprise_1, faker)
        children = []
        for j in range(3):
            children.append(create_department(test_client, dept, faker))
        dept_in_e1.append(dept)

    dept_in_e2 = []
    for i in range(4):
        dept_in_e2.append(create_department(test_client, enterprise_2, faker))

    resp = test_client.get(
        f"/v1/org_types/{org_type.code}/organization_tree",
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv

    assert len(rv) == 2
    assert len(rv[0]["children"]) == 2
    assert len(rv[1]["children"]) == 4

    for dept_ in rv[0]["children"]:
        assert len(dept_["children"]) == 3

    for dept_ in rv[1]["children"]:
        assert len(dept_["children"]) == 0


def create_user(
    test_client: TestClient,
    faker,
    organization_ids: list[str] | None = None,
    org_type_id: str | None = None,
):
    resp = test_client.post(
        "/v1/users",
        json=dict(
            name=faker.name(),
            username=faker.user_name(),
            mobile=faker.phone_number(),
            email=faker.email(),
            organization_ids=organization_ids,
            org_type_id=org_type_id,
        ),
    )
    user = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, user
    return CreateUserResult(**user)


def test_bind_users_to_organizations(test_client: TestClient, faker):
    resp = test_client.post("/v1/organizations/bind_users", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["user_ids"] == "该字段为必填项"
    assert error["detail"]["errors"]["organization_ids"] == "该字段为必填项"
    assert error["detail"]["errors"]["org_type_id"] == "该字段为必填项"

    resp = test_client.post(
        "/v1/organizations/bind_users",
        json={"user_ids": [], "organization_ids": []},
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["user_ids"] == "请至少选择一项"
    assert error["detail"]["errors"]["organization_ids"] == "请至少选择一项"

    org_type_1 = create_org_type(test_client, faker)
    enterprise_1_1 = create_enterprise(test_client, org_type_1, faker)
    enterprise_1_2 = create_enterprise(test_client, org_type_1, faker)
    dept_1_1_1 = create_department(test_client, enterprise_1_1, faker)
    dept_1_1_2 = create_department(test_client, enterprise_1_1, faker)
    dept_1_1_1_1 = create_department(test_client, dept_1_1_1, faker)

    org_type_2 = create_org_type(test_client, faker)
    enterprise_2_1 = create_enterprise(test_client, org_type_2, faker)
    dept_2_1_1 = create_department(test_client, enterprise_2_1, faker)

    user_1 = create_user(test_client, faker)
    user_2 = create_user(
        test_client,
        faker,
        organization_ids=[str(enterprise_1_1.id), str(dept_1_1_1_1.id)],
        org_type_id=str(org_type_1.id),
    )
    user_3 = create_user(
        test_client,
        faker,
        organization_ids=[str(dept_2_1_1.id)],
        org_type_id=str(org_type_2.id),
    )

    organization_ids: list[CreateEnterpriseResult | CreateDepartmentResult] = [
        enterprise_1_2,
        dept_1_1_2,
        dept_1_1_1_1,
        dept_2_1_1,
    ]
    resp = test_client.post(
        "/v1/organizations/bind_users",
        json={
            "user_ids": [str(u.id) for u in (user_1, user_2, user_3)],
            "organization_ids": [str(o.id) for o in organization_ids],
            "org_type_id": str(org_type_1.id),
        },
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv) == 2  # user1 and user2

    for user in rv:
        if user["id"] == str(user_1.id):
            assert len(user["departments"]) == 3
        else:
            assert len(user["departments"]) == 4

    resp = test_client.post(
        f"/v1/organizations/{org_type_1.id}/members", json={}
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2

    resp = test_client.post(
        f"/v1/organizations/{enterprise_1_1.id}/members", json={}
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2

    resp = test_client.post(
        f"/v1/organizations/{enterprise_1_1.id}/members",
        json={"include_sub_members": False},
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["id"] == str(user_2.id)
