from __future__ import annotations

import edgedb
import pytest

from ...query_api import (
    CreateDepartmentResult,
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    CreateRoleResult,
    CreateUserResult,
    create_department,
    create_enterprise,
    create_org_type,
    create_role,
    create_user,
    delete_org_type,
    delete_organization,
    get_department_by_id_or_code,
    get_enterprise_by_id_or_code,
    get_org_type_by_id_or_code,
    get_role_by_id_or_code,
    get_user_by_id,
    update_user_roles,
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


@pytest.fixture
async def role(
    edgedb_client: edgedb.AsyncIOClient, org_type: CreateOrgTypeResult, faker
) -> CreateRoleResult:
    return await create_role(
        edgedb_client,
        name=faker.company_prefix() + "经理",
        code=faker.lexify("?" * 10),
        description=faker.sentence(),
        org_type_id=org_type.id,
    )


@pytest.fixture
async def user(
    edgedb_client: edgedb.AsyncIOClient,
    role: CreateRoleResult,
    org_type: CreateOrgTypeResult,
    enterprise: CreateEnterpriseResult,
    faker,
) -> CreateUserResult:
    user = await create_user(
        edgedb_client,
        name=faker.name(),
        username=faker.user_name(),
        mobile=faker.phone_number(),
        email=faker.email(),
        hashed_password="password",
        organization_ids=[enterprise.id],
        org_type_id=org_type.id,
    )
    user = await update_user_roles(
        edgedb_client, id=user.id, role_ids=[role.id]
    )
    assert user
    return user


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
    edgedb_client: edgedb.AsyncIOClient,
    org_type: CreateOrgTypeResult,
    role: CreateRoleResult,
    enterprise: CreateEnterpriseResult,
    user: CreateUserResult,
    faker,
):
    assert enterprise
    assert role.org_type
    assert user.roles and user.departments

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

    assert not await get_role_by_id_or_code(
        edgedb_client,
        id=role.id,
        code=None,
    )

    updated_user = await get_user_by_id(
        edgedb_client,
        id=user.id,
    )
    assert updated_user
    assert not updated_user.roles
    assert not updated_user.departments


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
