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
            "上级部门ID格式错误",
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
    test_client: TestClient, enterprise: CreateEnterpriseResult, faker
) -> CreateDepartmentResult:
    data: dict[str, str] = {
        "parent_id": str(enterprise.id),
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
    assert (
        error["detail"]["message"]
        == "更新部门分支失败：缺少企业机构 ID 或 Code"
    )

    resp = test_client.put(
        f"/v1/departments/{old_code}",
        params={"enterprise_id_or_code": str(enterprise.id)},
        json=data,
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "更新部门分支失败：部门不存在"

    # update by code
    data["code"] = faker.hexify("^" * 6, upper=True)
    resp = test_client.put(
        f"/v1/departments/{department.code}",
        params={"enterprise_id_or_code": str(enterprise.id)},
        json=data,
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["id"] == str(department.id)
    assert rv["code"] == data["code"]
    old_code, department.code = department.code, rv["code"]

    resp = test_client.put(
        f"/v1/departments/{department.code}",
        params={"enterprise_id_or_code": enterprise.code},
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
        error["detail"]["message"]
        == "获取部门分支信息失败：缺少企业机构 ID 或 Code"
    )

    resp = test_client.get(
        f"/v1/departments/{department.code}",
        params={"enterprise_id_or_code": str(enterprise.id)},
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
