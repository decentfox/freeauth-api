from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from ...query_api import CreateEnterpriseResult, CreateOrgTypeResult
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
    test_client: TestClient, field: str | None, value: str | None, msg: str
):
    data: dict[str, str | None] = {}
    if field:
        data = {field: value}
    resp = test_client.post("/v1/enterprises", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"][field] == msg


@pytest.fixture
def org_type(test_client: TestClient, faker) -> CreateOrgTypeResult:
    return create_org_type(test_client, faker)


def test_create_enterprise(
    test_client: TestClient, org_type: CreateOrgTypeResult, faker
):
    data: dict[str, str] = {
        "org_type_id": "12345678-1234-5678-1234-567812345678",
        "name": faker.company(),
    }
    resp = test_client.post("/v1/enterprises", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "创建企业机构失败：组织类型不存在"

    data["org_type_id"] = str(org_type.id)
    resp = test_client.post("/v1/enterprises", json=data)
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
    resp = test_client.post("/v1/enterprises", json=data)
    enterprise = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, enterprise
    assert enterprise["name"] == data["name"]
    assert enterprise["code"] == data["code"].upper()
    assert enterprise["tax_id"] == data["tax_id"].upper()

    # same enterprise code for different org type
    new_org_type: CreateOrgTypeResult = create_org_type(test_client, faker)
    data["org_type_id"] = str(new_org_type.id)
    resp = test_client.post("/v1/enterprises", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, rv
    assert rv["code"] == enterprise["code"]

    data["org_type_id"] = str(org_type.id)
    resp = test_client.post("/v1/enterprises", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert (
        error["detail"]["errors"]["code"] == f"{enterprise['code']} 已被使用"
    )


def create_enterprise(
    test_client: TestClient, org_type: CreateOrgTypeResult, faker
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
    resp = test_client.post("/v1/enterprises", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.CREATED, rv
    return CreateEnterpriseResult(**rv)


@pytest.fixture
def enterprise(
    test_client: TestClient, org_type: CreateOrgTypeResult, faker
) -> CreateEnterpriseResult:
    return create_enterprise(test_client, org_type, faker)


def test_update_enterprise(
    test_client: TestClient,
    org_type: CreateOrgTypeResult,
    enterprise: CreateEnterpriseResult,
    faker,
):
    # validating error
    data: dict[str, str] = {}
    resp = test_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["name"] == "该字段为必填项"

    data = {
        "name": faker.company(),
        "tax_id": "invalid tax id",
    }
    resp = test_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
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
    resp = test_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["name"] == data["name"]
    assert rv["code"] == data["code"]
    old_code, enterprise.code = enterprise.code, rv["code"]

    # old code not found
    resp = test_client.put(f"/v1/enterprises/{old_code}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "更新企业机构失败：企业机构不存在"

    # update by code
    data["code"] = faker.hexify("^" * 6, upper=True)
    resp = test_client.put(f"/v1/enterprises/{enterprise.code}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["id"] == str(enterprise.id)
    assert rv["code"] == data["code"]
    old_code, enterprise.code = enterprise.code, rv["code"]

    # same enterprise code for different org type
    new_org_type = create_org_type(test_client, faker)
    enterprise_1 = create_enterprise(test_client, new_org_type, faker)
    enterprise_2 = create_enterprise(test_client, org_type, faker)

    data = {
        "name": enterprise.name,
        "code": enterprise_1.code,
    }
    resp = test_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["code"] == enterprise_1.code

    data = {
        "name": enterprise.name,
        "code": enterprise_2.code,
    }
    resp = test_client.put(f"/v1/enterprises/{enterprise.id}", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.BAD_REQUEST, error
    assert error["detail"]["errors"]["code"] == f"{enterprise_2.code} 已被使用"


def test_delete_enterprises(test_client: TestClient, faker):
    data: dict[str, list] = {}
    resp = test_client.request("DELETE", "/v1/enterprises", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    error["detail"]["errors"]["ids"] = "该字段为必填项"

    data = {"ids": ["invalid_id"]}
    resp = test_client.request("DELETE", "/v1/enterprises", json=data)
    error = resp.json()
    assert error["detail"]["errors"]["ids.0"] == "企业机构ID格式错误"

    data = {
        "ids": ["12345678-1234-5678-1234-567812345678"],
    }
    resp = test_client.request("DELETE", "/v1/enterprises", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert len(resp.json()["enterprises"]) == 0

    org_type_1 = create_org_type(test_client, faker)
    org_type_2 = create_org_type(test_client, faker)
    e_1 = create_enterprise(test_client, org_type_1, faker)
    e_2 = create_enterprise(test_client, org_type_2, faker)
    e_3 = create_enterprise(test_client, org_type_2, faker)

    ids = [str(e_1.id), str(e_2.id), str(e_3.id)]
    data = {"ids": ids}
    resp = test_client.request("DELETE", "/v1/enterprises", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert sorted(e["id"] for e in resp.json()["enterprises"]) == sorted(ids)


def test_get_enterprise(
    test_client: TestClient, enterprise: CreateEnterpriseResult
):
    not_found_id = "12345678-1234-5678-1234-567812345678"
    resp = test_client.get(f"/v1/enterprises/{not_found_id}")
    error = resp.json()
    assert resp.status_code == HTTPStatus.NOT_FOUND, error
    assert error["detail"]["message"] == "获取企业机构信息失败：企业机构不存在"

    resp = test_client.get(f"/v1/enterprises/{enterprise.id}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateEnterpriseResult(**resp.json()) == enterprise

    resp = test_client.get(f"/v1/enterprises/{enterprise.code}")
    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert CreateEnterpriseResult(**resp.json()) == enterprise


def test_query_enterprises_in_org_type(test_client: TestClient, faker):
    org_type_1 = create_org_type(test_client, faker)
    org_type_2 = create_org_type(test_client, faker)
    enterprises_in_ot1 = []
    for _ in range(2):
        enterprises_in_ot1.append(
            create_enterprise(test_client, org_type_1, faker)
        )
    enterprises_in_ot2 = []
    for _ in range(4):
        enterprises_in_ot2.append(
            create_enterprise(test_client, org_type_2, faker)
        )

    data: dict = {}
    resp = test_client.post(
        f"/v1/org_types/{org_type_1.id}/enterprises/query", json=data
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 2

    resp = test_client.post(
        f"/v1/org_types/{org_type_2.id}/enterprises/query", json=data
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 4

    data["order_by"] = ["-code"]
    resp = test_client.post(
        f"/v1/org_types/{org_type_2.id}/enterprises/query", json=data
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert sorted(
        [e.code or "" for e in enterprises_in_ot2], reverse=True
    ) == [e["code"] for e in rv["rows"]]

    data["q"] = enterprises_in_ot2[0].code
    resp = test_client.post(
        f"/v1/org_types/{org_type_2.id}/enterprises/query", json=data
    )
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["total"] == 1
    assert rv["rows"][0]["code"] == enterprises_in_ot2[0].code
