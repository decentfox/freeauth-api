from __future__ import annotations

import edgedb
import pytest

from ...query_api import (
    CreateDepartmentResult,
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    create_department,
    create_enterprise,
    create_org_type,
    delete_org_type,
    delete_organization,
    get_department_by_id_or_code,
    get_enterprise_by_id_or_code,
    get_org_type_by_id_or_code,
)


@pytest.fixture
async def org_type(
    edgedb_client: edgedb.AsyncIOClient, faker
) -> CreateOrgTypeResult:
    return await create_org_type(
        edgedb_client,
        name=faker.company_prefix(),
        code=faker.hexify("^" * 6, upper=True),
        description=faker.sentence(),
    )


@pytest.fixture
async def enterprise(
    edgedb_client: edgedb.AsyncIOClient, org_type: CreateOrgTypeResult, faker
) -> CreateEnterpriseResult | None:
    return await create_enterprise(
        edgedb_client,
        name=faker.company(),
        code=faker.hexify("^" * 6, upper=True),
        tax_id=faker.hexify("^" * 18, upper=True),
        issuing_bank=faker.company(),
        bank_account_number=faker.ssn(),
        contact_address=faker.address(),
        contact_phone_num=faker.phone_number(),
        org_type_id=org_type.id,
    )


async def create_department_branch(
    edgedb_client: edgedb.AsyncIOClient,
    parent: CreateEnterpriseResult | CreateDepartmentResult,
    faker,
) -> CreateDepartmentResult:
    dept = await create_department(
        edgedb_client,
        name=faker.company_prefix(),
        code=faker.hexify("^" * 6, upper=True),
        description=faker.sentence(),
        parent_id=parent.id,
    )
    assert dept is not None
    return dept


@pytest.mark.asyncio
async def test_delete_org_type(
    edgedb_client: edgedb.AsyncIOClient, org_type, enterprise, faker
):
    assert enterprise

    dept_1 = await create_department_branch(edgedb_client, enterprise, faker)
    dept_2 = await create_department_branch(edgedb_client, enterprise, faker)
    dept_1_1 = await create_department_branch(edgedb_client, dept_1, faker)

    rv = await delete_org_type(edgedb_client, ids=[org_type.id])
    assert len(rv) == 1
    assert rv[0].name == org_type.name
    assert rv[0].code == org_type.code

    deleted_org_type = await get_org_type_by_id_or_code(
        edgedb_client, id=org_type.id, code=None
    )
    assert not deleted_org_type

    deleted_enterprise = await get_enterprise_by_id_or_code(
        edgedb_client,
        id=enterprise.id,
        code=None,
        org_type_id=None,
        org_type_code=None,
    )
    assert not deleted_enterprise

    for dept in (dept_1, dept_1_1, dept_2):
        deleted_dept = await get_department_by_id_or_code(
            edgedb_client,
            id=dept.id,
            code=None,
            enterprise_id=None,
        )
        assert not deleted_dept


@pytest.mark.asyncio
async def test_delete_enterprise(
    edgedb_client: edgedb.AsyncIOClient, org_type, enterprise, faker
):
    dept_1 = await create_department_branch(edgedb_client, enterprise, faker)
    dept_2 = await create_department_branch(edgedb_client, enterprise, faker)
    dept_1_1 = await create_department_branch(edgedb_client, dept_1, faker)

    rv = await delete_organization(edgedb_client, ids=[enterprise.id])
    assert len(rv) == 1
    assert rv[0].id == enterprise.id

    deleted_enterprise = await get_enterprise_by_id_or_code(
        edgedb_client,
        id=enterprise.id,
        code=None,
        org_type_id=None,
        org_type_code=None,
    )
    assert not deleted_enterprise

    for dept in (dept_1, dept_1_1, dept_2):
        deleted_dept = await get_department_by_id_or_code(
            edgedb_client,
            id=dept.id,
            code=None,
            enterprise_id=None,
        )
        assert not deleted_dept


@pytest.mark.asyncio
async def test_delete_department(
    edgedb_client: edgedb.AsyncIOClient, org_type, enterprise, faker
):
    dept_1 = await create_department_branch(edgedb_client, enterprise, faker)
    dept_1_1 = await create_department_branch(edgedb_client, dept_1, faker)

    rv = await delete_organization(edgedb_client, ids=[dept_1.id])
    assert len(rv) == 1
    assert rv[0].id == dept_1.id

    for dept in (dept_1, dept_1_1):
        deleted_dept = await get_department_by_id_or_code(
            edgedb_client,
            id=dept.id,
            code=None,
            enterprise_id=None,
        )
        assert not deleted_dept
