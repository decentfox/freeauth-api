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

from http import HTTPStatus
from typing import Any

import pytest
from fastapi.testclient import TestClient

from freeauth.db.admin.admin_qry_async_edgeql import CreateOrgTypeResult


@pytest.mark.parametrize(
    "field,value,msg",
    [
        (
            "name",
            "很长的名字" * 5,
            "最大支持的长度为20个字符",
        ),
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
        (
            "code",
            None,
            "该字段不得为空",
        ),
        (
            "code",
            "",
            "该字段为必填项",
        ),
        (
            "code",
            "   ",
            "该字段为必填项",
        ),
    ],
)
def test_create_org_type_validate_errors(
    bo_client: TestClient, field: str | None, value: str | None, msg: str
):
    data: dict[str, str | None] = {}
    if field:
        data = {field: value}
    resp = bo_client.post("/v1/org_types", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


def test_create_org_type(bo_client: TestClient):
    data: dict[str, str] = {"name": "集团", "code": "org_type"}
    resp = bo_client.post("/v1/org_types", json=data)
    org_type = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, org_type
    assert org_type["name"] == "集团"
    assert org_type["code"] == "ORG_TYPE"
    assert not org_type["is_deleted"]
    assert not org_type["is_protected"]
    assert not org_type["description"]

    data["description"] = "集团描述"
    resp = bo_client.post("/v1/org_types", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == "ORG_TYPE 已被使用"


def create_org_type(bo_client: TestClient, faker) -> CreateOrgTypeResult:
    resp = bo_client.post(
        "/v1/org_types",
        json={
            "name": faker.company_prefix(),
            "code": faker.hexify("^" * 6, upper=True),
            "description": faker.sentence(),
        },
    )
    return CreateOrgTypeResult(**resp.json())


@pytest.fixture
def org_type(bo_client: TestClient, faker) -> CreateOrgTypeResult:
    return create_org_type(bo_client, faker)


@pytest.fixture
def default_org_type(bo_client: TestClient) -> CreateOrgTypeResult:
    resp = bo_client.get("/v1/org_types/INNER")
    return CreateOrgTypeResult(**resp.json())


def test_update_org_type(
    bo_client: TestClient,
    org_type: CreateOrgTypeResult,
    default_org_type,
):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = bo_client.put(f"/v1/org_types/{not_found_id}", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "更新组织类型失败：组织类型不存在"

    data: dict[str, Any] = {}
    resp = bo_client.put(f"/v1/org_types/{org_type.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert CreateOrgTypeResult(**rv) == org_type

    data = {
        "name": "    ",
        "code": "    ",
        "description": "    ",
        "is_deleted": True,
    }
    resp = bo_client.put(f"/v1/org_types/{org_type.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["name"] == org_type.name
    assert rv["description"] == org_type.description
    assert rv["is_deleted"]

    data = {
        "name": "    合作商家",
        "code": "   new_code",
        "description": "    商家描述",
    }
    resp = bo_client.put(f"/v1/org_types/{org_type.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["name"] == "合作商家"
    assert rv["code"] == "NEW_CODE"
    assert rv["description"] == "商家描述"

    data["name"] = "很长的名字" * 5
    resp = bo_client.put(f"/v1/org_types/{org_type.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["name"] == "最大支持的长度为20个字符"

    data = {
        "name": "默认内部组织",
        "code": default_org_type.code,
        "description": "系统默认组织类型",
        "is_deleted": True,
    }
    resp = bo_client.put(f"/v1/org_types/{default_org_type.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["name"] == "默认内部组织"
    assert rv["description"] == "系统默认组织类型"
    assert not rv["is_deleted"]

    data = {"code": default_org_type.code}
    resp = bo_client.put(f"/v1/org_types/{org_type.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert (
        error["detail"]["errors"]["code"]
        == f"{default_org_type.code} 已被使用"
    )


def test_get_org_type(bo_client: TestClient, org_type: CreateOrgTypeResult):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = bo_client.get(f"/v1/org_types/{not_found_id}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取组织类型信息失败：组织类型不存在"

    resp = bo_client.get(f"/v1/org_types/{org_type.id}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateOrgTypeResult(**resp.json()) == org_type


def test_toggle_org_type_status(
    bo_client: TestClient, org_type: CreateOrgTypeResult, default_org_type
):
    data: dict[str, Any] = {}
    resp = bo_client.put("/v1/org_types/status", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data = {
        "ids": ["invalid_id"],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/org_types/status", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "ID格式错误"

    data = {
        "ids": ["12345678-1234-5678-1234-567812345678"],
        "is_deleted": False,
    }
    resp = bo_client.put("/v1/org_types/status", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["org_types"] == []

    data = {
        "ids": [str(org_type.id)],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/org_types/status", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["org_types"]) == 1
    assert rv["org_types"][0] == {
        "id": str(org_type.id),
        "name": org_type.name,
        "code": org_type.code,
        "is_deleted": True,
    }

    data = {
        "ids": [str(org_type.id)],
        "is_deleted": False,
    }
    resp = bo_client.put("/v1/org_types/status", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["org_types"]) == 1
    assert rv["org_types"][0] == {
        "id": str(org_type.id),
        "name": org_type.name,
        "code": org_type.code,
        "is_deleted": False,
    }

    data = {
        "ids": [str(default_org_type.id)],
        "is_deleted": True,
    }
    resp = bo_client.put("/v1/org_types/status", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["org_types"]) == 0


def test_delete_org_types(
    bo_client: TestClient,
    org_type: CreateOrgTypeResult,
    default_org_type,
    faker,
):
    data: dict[str, Any] = {}
    resp = bo_client.request("DELETE", "/v1/org_types", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    for msg in error["detail"]["errors"].values():
        assert msg == "该字段为必填项"

    data = {
        "ids": ["invalid_id"],
    }
    resp = bo_client.request("DELETE", "/v1/org_types", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "ID格式错误"

    data = {
        "ids": ["12345678-1234-5678-1234-567812345678"],
    }
    resp = bo_client.request("DELETE", "/v1/org_types", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert len(resp.json()["org_types"]) == 0

    org_type1 = create_org_type(bo_client, faker)
    org_type2 = create_org_type(bo_client, faker)

    ids = [str(org_type.id), str(org_type1.id), str(org_type2.id)]
    data = {"ids": ids}
    resp = bo_client.request("DELETE", "/v1/org_types", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert sorted(
        org_type["id"] for org_type in resp.json()["org_types"]
    ) == sorted(ids)

    data = {
        "ids": [str(default_org_type.id)],
    }
    resp = bo_client.request("DELETE", "/v1/org_types", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert len(resp.json()["org_types"]) == 0


def test_get_org_types(
    bo_client: TestClient, default_org_type, org_type: CreateOrgTypeResult
):
    resp = bo_client.get("/v1/org_types")
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert len(rv["org_types"]) == 2
