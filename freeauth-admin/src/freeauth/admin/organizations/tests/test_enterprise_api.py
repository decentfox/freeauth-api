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

import pytest
from fastapi.testclient import TestClient

from freeauth.db.admin.admin_qry_async_edgeql import (
    CreateEnterpriseResult,
    CreateOrgTypeResult,
)

from .test_org_type_api import create_org_type


@pytest.mark.parametrize(
    "field,value,msg",
    [
        (
            "org_type_id",
            "",
            "企业机构ID格式错误",
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
        (
            "tax_id",
            "invalid tax id",
            "纳税识别号格式有误，仅支持15、18 或 20 位数字与字母",
        ),
    ],
)
def test_create_enterprise_validate_errors(
    bo_client: TestClient, field: str | None, value: str | None, msg: str
):
    data: dict[str, str | None] = {}
    if field:
        data = {field: value}
    resp = bo_client.post("/v1/enterprises", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


@pytest.fixture
def org_type(bo_client: TestClient, faker) -> CreateOrgTypeResult:
    return create_org_type(bo_client, faker)


def test_create_enterprise(
    bo_client: TestClient, org_type: CreateOrgTypeResult, faker
):
    data: dict[str, str] = {
        "org_type_id": "12345678-1234-5678-1234-567812345678",
        "name": faker.company(),
    }
    resp = bo_client.post("/v1/enterprises", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "创建企业机构失败：组织类型不存在"

    data["org_type_id"] = str(org_type.id)
    resp = bo_client.post("/v1/enterprises", json=data)
    enterprise = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, enterprise
    assert enterprise["name"] == data["name"]
    assert not enterprise["code"]
    assert not enterprise["tax_id"]

    data.update(
        {
            "code": faker.hexify("^" * 6),
            "tax_id": faker.hexify("^" * 18),
            "issuing_bank": faker.company(),
            "bank_account_number": faker.ssn(),
            "contact_address": faker.address(),
            "contact_phone_num": faker.phone_number(),
        }
    )
    resp = bo_client.post("/v1/enterprises", json=data)
    enterprise = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, enterprise
    assert enterprise["name"] == data["name"]
    assert enterprise["code"] == data["code"].upper()
    assert enterprise["tax_id"] == data["tax_id"].upper()

    # same enterprise code for different org type
    new_org_type: CreateOrgTypeResult = create_org_type(bo_client, faker)
    data["org_type_id"] = str(new_org_type.id)
    resp = bo_client.post("/v1/enterprises", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, rv
    assert rv["code"] == enterprise["code"]

    data["org_type_id"] = str(org_type.id)
    resp = bo_client.post("/v1/enterprises", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert (
        error["detail"]["errors"]["code"] == f"{enterprise['code']} 已被使用"
    )


def create_enterprise(
    bo_client: TestClient, org_type: CreateOrgTypeResult, faker
) -> CreateEnterpriseResult:
    data: dict[str, str] = {
        "org_type_id": str(org_type.id),
        "name": faker.company(),
        "code": faker.hexify("^" * 6, upper=True),
        "tax_id": faker.hexify("^" * 18, upper=True),
        "issuing_bank": faker.company(),
        "bank_account_number": faker.ssn(),
        "contact_address": faker.address(),
        "contact_phone_num": faker.phone_number(),
    }
    resp = bo_client.post("/v1/enterprises", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, rv
    return CreateEnterpriseResult(**rv)


@pytest.fixture
def enterprise(
    bo_client: TestClient, org_type: CreateOrgTypeResult, faker
) -> CreateEnterpriseResult:
    return create_enterprise(bo_client, org_type, faker)


def test_update_enterprise(
    bo_client: TestClient,
    org_type: CreateOrgTypeResult,
    enterprise: CreateEnterpriseResult,
    faker,
):
    # validating error
    data: dict[str, str] = {}
    resp = bo_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["name"] == "该字段为必填项"

    data = {
        "name": faker.company(),
        "tax_id": "invalid tax id",
    }
    resp = bo_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert (
        error["detail"]["errors"]["tax_id"]
        == "纳税识别号格式有误，仅支持15、18 或 20 位数字与字母"
    )

    # update by ID
    data = {
        "name": faker.company(),
        "code": faker.hexify("^" * 6, upper=True),
    }
    resp = bo_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["name"] == data["name"]
    assert rv["code"] == data["code"]
    old_code, enterprise.code = enterprise.code, rv["code"]

    # old code not found
    resp = bo_client.put(f"/v1/enterprises/{old_code}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert (
        error["detail"]["message"]
        == "更新企业机构失败：缺少组织类型 ID 或 Code"
    )

    resp = bo_client.put(
        f"/v1/enterprises/{old_code}",
        params={"org_type_id_or_code": str(org_type.id)},
        json=data,
    )
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "更新企业机构失败：企业机构不存在"

    # update by code
    data["code"] = faker.hexify("^" * 6, upper=True)
    resp = bo_client.put(
        f"/v1/enterprises/{enterprise.code}",
        params={"org_type_id_or_code": str(org_type.id)},
        json=data,
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["id"] == str(enterprise.id)
    assert rv["code"] == data["code"]
    old_code, enterprise.code = enterprise.code, rv["code"]

    resp = bo_client.put(
        f"/v1/enterprises/{enterprise.code}",
        params={"org_type_id_or_code": org_type.code},
        json=data,
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv

    # same enterprise code for different org type
    new_org_type = create_org_type(bo_client, faker)
    enterprise_1 = create_enterprise(bo_client, new_org_type, faker)
    enterprise_2 = create_enterprise(bo_client, org_type, faker)

    data = {
        "name": enterprise.name,
        "code": enterprise_1.code,
    }
    resp = bo_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["code"] == enterprise_1.code

    data = {
        "name": enterprise.name,
        "code": enterprise_2.code,
    }
    resp = bo_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{enterprise_2.code} 已被使用"


def test_delete_enterprises(bo_client: TestClient, faker):
    data: dict[str, list] = {}
    resp = bo_client.request("DELETE", "/v1/organizations", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    error["detail"]["errors"]["ids"] = "该字段为必填项"

    data = {"ids": ["invalid_id"]}
    resp = bo_client.request("DELETE", "/v1/organizations", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "ID格式错误"

    data = {
        "ids": ["12345678-1234-5678-1234-567812345678"],
    }
    resp = bo_client.request("DELETE", "/v1/organizations", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert len(resp.json()["organizations"]) == 0

    org_type_1 = create_org_type(bo_client, faker)
    org_type_2 = create_org_type(bo_client, faker)
    e_1 = create_enterprise(bo_client, org_type_1, faker)
    e_2 = create_enterprise(bo_client, org_type_2, faker)
    e_3 = create_enterprise(bo_client, org_type_2, faker)

    ids = [str(e_1.id), str(e_2.id), str(e_3.id)]
    data = {"ids": ids}
    resp = bo_client.request("DELETE", "/v1/organizations", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert sorted(e["id"] for e in resp.json()["organizations"]) == sorted(ids)


def test_get_enterprise(
    bo_client: TestClient,
    enterprise: CreateEnterpriseResult,
    org_type: CreateOrgTypeResult,
):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = bo_client.get(f"/v1/enterprises/{not_found_id}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取企业机构信息失败：企业机构不存在"

    resp = bo_client.get(f"/v1/enterprises/{enterprise.id}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateEnterpriseResult(**resp.json()) == enterprise

    resp = bo_client.get(f"/v1/enterprises/{enterprise.code}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert (
        error["detail"]["message"]
        == "获取企业机构信息失败：缺少组织类型 ID 或 Code"
    )

    resp = bo_client.get(
        f"/v1/enterprises/{enterprise.code}",
        params={"org_type_id_or_code": str(org_type.id)},
    )
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateEnterpriseResult(**resp.json()) == enterprise


def test_query_enterprises_in_org_type(bo_client: TestClient, faker):
    org_type_1 = create_org_type(bo_client, faker)
    org_type_2 = create_org_type(bo_client, faker)
    enterprises_in_ot1 = []
    for _ in range(2):
        enterprises_in_ot1.append(
            create_enterprise(bo_client, org_type_1, faker)
        )
    enterprises_in_ot2 = []
    for _ in range(4):
        enterprises_in_ot2.append(
            create_enterprise(bo_client, org_type_2, faker)
        )

    data: dict = {}
    resp = bo_client.post("/v1/enterprises/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 6

    data["org_type_id"] = str(org_type_1.id)
    resp = bo_client.post("/v1/enterprises/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2

    data["org_type_id"] = str(org_type_2.id)
    resp = bo_client.post("/v1/enterprises/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 4

    data["order_by"] = ["-code"]
    resp = bo_client.post("/v1/enterprises/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted(
        [e.code or "" for e in enterprises_in_ot2], reverse=True
    ) == [e["code"] for e in rv["rows"]]

    data["q"] = enterprises_in_ot2[0].code
    resp = bo_client.post("/v1/enterprises/query", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["code"] == enterprises_in_ot2[0].code
