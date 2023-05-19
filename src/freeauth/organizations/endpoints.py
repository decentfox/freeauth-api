from __future__ import annotations

import uuid
from dataclasses import asdict
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException

from .. import get_edgedb_client
from ..app import router
from ..dataclasses import PaginatedData
from ..query_api import (
    CreateDepartmentResult,
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    CreateUserResult,
    DeleteOrganizationResult,
    DeleteOrgTypeResult,
    GetOrganizationNodeResult,
    UpdateOrgTypeStatusResult,
    create_department,
    create_enterprise,
    create_org_type,
    delete_org_type,
    delete_organization,
    get_department_by_id_or_code,
    get_enterprise_by_id_or_code,
    get_org_type_by_id_or_code,
    get_organization_node,
    organization_bind_users,
    organization_unbind_users,
    query_org_types,
    update_department,
    update_enterprise,
    update_org_type,
    update_org_type_status,
)
from .dataclasses import (
    DepartmentPostOrPutBody,
    EnterprisePostBody,
    EnterprisePutBody,
    EnterpriseQueryBody,
    OrganizationDeleteBody,
    OrganizationNode,
    OrganizationUnbindUserBody,
    OrganizationUserBody,
    OrganizationUserQueryBody,
    OrgTypeDeleteBody,
    OrgTypePostBody,
    OrgTypePutBody,
    OrgTypeStatusBody,
)
from .dependencies import (
    parse_department_id_or_code,
    parse_enterprise_id_or_code,
    parse_org_type_id_or_code,
)


@router.post(
    "/org_types",
    status_code=HTTPStatus.CREATED,
    tags=["组织管理"],
    summary="创建组织类型",
    description="包含字段：名称（必填）、Code（必填）、描述（选填）",
)
async def post_org_type(
    body: OrgTypePostBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateOrgTypeResult:
    try:
        org_type = await create_org_type(
            client,
            name=body.name,
            code=body.code,
            description=body.description,
        )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return org_type


@router.put(
    "/org_types/status",
    tags=["组织管理"],
    summary="变更组织类型状态",
    description="批量变更组织类型状态",
)
async def toggle_org_types_status(
    body: OrgTypeStatusBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> dict[str, list[UpdateOrgTypeStatusResult]]:
    updated_org_types: list[UpdateOrgTypeStatusResult] = (
        await update_org_type_status(
            client, ids=body.ids, is_deleted=body.is_deleted
        )
    )
    return {"org_types": updated_org_types}


@router.delete(
    "/org_types",
    tags=["组织管理"],
    summary="删除组织类型",
    description="批量删除组织类型",
)
async def delete_org_types(
    body: OrgTypeDeleteBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> dict[str, list[DeleteOrgTypeResult]]:
    deleted_org_types: list[DeleteOrgTypeResult] = await delete_org_type(
        client, ids=body.ids
    )
    return {"org_types": deleted_org_types}


@router.get(
    "/org_types/{id_or_code}",
    tags=["组织管理"],
    summary="获取组织类型信息",
    description="获取指定组织类型的信息",
)
async def get_org_type(
    id_or_code: uuid.UUID | str = Depends(parse_org_type_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateOrgTypeResult:
    org_type: CreateOrgTypeResult | None = await get_org_type_by_id_or_code(
        client,
        id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
        code=id_or_code if isinstance(id_or_code, str) else None,
    )
    if not org_type:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="组织类型不存在"
        )
    return org_type


@router.put(
    "/org_types/{id_or_code}",
    tags=["组织管理"],
    summary="更新组织类型",
    description="更新指定组织类型的信息",
)
async def put_org_type(
    body: OrgTypePutBody,
    id_or_code: uuid.UUID | str = Depends(parse_org_type_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateOrgTypeResult:
    try:
        org_type: CreateOrgTypeResult | None = await update_org_type(
            client,
            name=body.name,
            code=body.code,
            description=body.description,
            is_deleted=body.is_deleted,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            current_code=id_or_code if isinstance(id_or_code, str) else None,
        )
        if not org_type:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="组织类型不存在"
            )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return org_type


@router.get(
    "/org_types",
    tags=["组织管理"],
    summary="获取组织类型列表",
    description="获取全部组织类型信息",
)
async def get_org_types(
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> dict[str, list[CreateOrgTypeResult]]:
    org_types: list[CreateOrgTypeResult] = await query_org_types(client)
    return {"org_types": org_types}


@router.post(
    "/enterprises",
    status_code=HTTPStatus.CREATED,
    tags=["组织管理"],
    summary="创建企业机构",
    description="创建指定组织类型的企业机构",
)
async def post_enterprise(
    body: EnterprisePostBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateEnterpriseResult:
    try:
        enterprise: CreateEnterpriseResult | None = await create_enterprise(
            client,
            name=body.name,
            code=body.code,
            tax_id=body.tax_id,
            issuing_bank=body.issuing_bank,
            bank_account_number=body.bank_account_number,
            contact_address=body.contact_address,
            contact_phone_num=body.contact_phone_num,
            org_type_id=body.org_type_id,
        )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    if not enterprise:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="组织类型不存在"
        )
    return enterprise


@router.put(
    "/enterprises/{id_or_code}",
    tags=["组织管理"],
    summary="更新企业机构",
    description="通过企业机构 ID 或 Code，更新企业机构信息",
)
async def put_enterprise(
    body: EnterprisePutBody,
    params: tuple[str | uuid.UUID, str | uuid.UUID | None] = Depends(
        parse_enterprise_id_or_code
    ),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateEnterpriseResult:
    id_or_code, ot_id_or_code = params
    try:
        enterprise: CreateEnterpriseResult | None = await update_enterprise(
            client,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            current_code=id_or_code if isinstance(id_or_code, str) else None,
            org_type_id=(
                ot_id_or_code if isinstance(ot_id_or_code, uuid.UUID) else None
            ),
            org_type_code=(
                ot_id_or_code if isinstance(ot_id_or_code, str) else None
            ),
            name=body.name,
            code=body.code,
            tax_id=body.tax_id,
            issuing_bank=body.issuing_bank,
            bank_account_number=body.bank_account_number,
            contact_address=body.contact_address,
            contact_phone_num=body.contact_phone_num,
        )
        if not enterprise:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="企业机构不存在"
            )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return enterprise


@router.delete(
    "/organizations",
    tags=["组织管理"],
    summary="删除企业机构或部门分支",
    description="批量删除企业机构或部门分支",
)
async def delete_organizations(
    body: OrganizationDeleteBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> dict[str, list[DeleteOrganizationResult]]:
    deleted_organizations: list[DeleteOrganizationResult] = (
        await delete_organization(client, ids=body.ids)
    )
    return {"organizations": deleted_organizations}


@router.get(
    "/enterprises/{id_or_code}",
    tags=["组织管理"],
    summary="获取企业机构信息",
    description="通过企业机构 ID 或 Code，获取指定企业机构的信息",
)
async def get_enterprise(
    params: tuple[str | uuid.UUID, str | uuid.UUID | None] = Depends(
        parse_enterprise_id_or_code
    ),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateEnterpriseResult:
    id_or_code, ot_id_or_code = params
    enterprise: CreateEnterpriseResult | None = (
        await get_enterprise_by_id_or_code(
            client,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            code=id_or_code if isinstance(id_or_code, str) else None,
            org_type_id=(
                ot_id_or_code if isinstance(ot_id_or_code, uuid.UUID) else None
            ),
            org_type_code=(
                ot_id_or_code if isinstance(ot_id_or_code, str) else None
            ),
        )
    )
    if not enterprise:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="企业机构不存在"
        )
    return enterprise


@router.post(
    "/enterprises/query",
    tags=["组织管理"],
    summary="获取企业机构列表",
    description="分页获取，支持关键字搜索、排序，支持过滤指定组织类型下的企业机构",
)
async def get_enterprises_in_org_type(
    body: EnterpriseQueryBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                org_type_id := <optional uuid>$org_type_id,
                enterprises := (
                    SELECT Enterprise
                    FILTER (
                        true IF not EXISTS q ELSE
                        .name ILIKE q OR
                        .code ?? '' ILIKE q OR
                        .tax_id ?? '' ILIKE q OR
                        .issuing_bank ?? '' ILIKE q OR
                        .bank_account_number ?? '' ILIKE q OR
                        .contact_address ?? '' ILIKE q OR
                        .contact_phone_num ?? '' ILIKE q
                    ) AND (
                        true IF not EXISTS org_type_id ELSE
                        .org_type.id = org_type_id
                    )
                ),
                total := count(enterprises)

            SELECT (
                total := total,
                per_page := per_page,
                page := page,
                last := math::ceil(total / per_page),
                rows := array_agg((
                    SELECT enterprises {{
                        id,
                        name,
                        code,
                        tax_id,
                        issuing_bank,
                        bank_account_number,
                        contact_address,
                        contact_phone_num,
                        org_type := (
                            SELECT .org_type {{id, code, name}}
                        )
                    }}
                    ORDER BY {body.ordering_expr}
                    OFFSET (page - 1) * per_page
                    LIMIT per_page
                ))
            );\
            """,
        q=f"%{body.q}%" if body.q else None,
        page=body.page,
        per_page=body.per_page,
        org_type_id=body.org_type_id,
    )
    return PaginatedData.parse_raw(result)


@router.post(
    "/departments",
    status_code=HTTPStatus.CREATED,
    tags=["组织管理"],
    summary="创建部门分支",
    description="创建属于指定父部门或企业机构的部门分支",
)
async def post_department(
    body: DepartmentPostOrPutBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateDepartmentResult:
    try:
        department: CreateDepartmentResult | None = await create_department(
            client,
            name=body.name,
            code=body.code,
            description=body.description,
            parent_id=body.parent_id,
        )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    if not department:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="上级部门或企业机构不存在"
        )
    return department


@router.put(
    "/departments/{id_or_code}",
    tags=["组织管理"],
    summary="更新部门分支",
    description="通过部门 ID 或 Code，更新部门分支信息",
)
async def put_department(
    body: DepartmentPostOrPutBody,
    params: tuple[str | uuid.UUID, uuid.UUID | None] = Depends(
        parse_department_id_or_code
    ),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateDepartmentResult:
    id_or_code, enterprise_id = params
    try:
        department: CreateDepartmentResult | None = await update_department(
            client,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            current_code=id_or_code if isinstance(id_or_code, str) else None,
            enterprise_id=enterprise_id,
            name=body.name,
            code=body.code,
            description=body.description,
            parent_id=body.parent_id,
        )
        if not department:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="部门不存在"
            )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return department


@router.get(
    "/departments/{id_or_code}",
    tags=["组织管理"],
    summary="获取部门分支信息",
    description="通过部门 ID 或 Code，获取指定部门分支的信息",
)
async def get_department(
    params: tuple[str | uuid.UUID, uuid.UUID | None] = Depends(
        parse_department_id_or_code
    ),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateDepartmentResult:
    id_or_code, enterprise_id = params
    department: CreateDepartmentResult | None = (
        await get_department_by_id_or_code(
            client,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            code=id_or_code if isinstance(id_or_code, str) else None,
            enterprise_id=enterprise_id,
        )
    )
    if not department:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="部门不存在"
        )
    return department


@router.get(
    "/org_types/{id_or_code}/organization_tree",
    tags=["组织管理"],
    summary="获取组织树",
    description="通过组织类型 ID 或 Code，获取组织树信息",
)
async def get_organization_tree_by_org_type(
    id_or_code: uuid.UUID | str = Depends(parse_org_type_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[OrganizationNode]:
    async def get_child_nodes(
        parent_id: uuid.UUID | None = None,
    ) -> list[OrganizationNode]:
        children: list[OrganizationNode] = []
        nodes: list[GetOrganizationNodeResult] = await get_organization_node(
            client,
            org_type_id=(
                id_or_code if isinstance(id_or_code, uuid.UUID) else None
            ),
            org_type_code=id_or_code if isinstance(id_or_code, str) else None,
            parent_id=parent_id,
        )
        for child in nodes:
            node = OrganizationNode(children=[], **asdict(child))
            if node.has_children:
                node.children = await get_child_nodes(node.id)
            children.append(node)
        return children

    return await get_child_nodes()


@router.post(
    "/organizations/bind_users",
    tags=["组织管理"],
    summary="添加成员",
    description="添加成员到一个或多个部门分支、企业机构中，支持添加多个成员",
)
async def bind_users_to_organizations(
    body: OrganizationUserBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[CreateUserResult]:
    return await organization_bind_users(
        client,
        user_ids=body.user_ids,
        organization_ids=body.organization_ids,
        org_type_id=body.org_type_id,
    )


@router.post(
    "/organizations/unbind_users",
    tags=["组织管理"],
    summary="移除成员",
    description="从一个或多个部门分支、企业机构中移除一个或多个成员",
)
async def unbind_users_to_organizations(
    body: OrganizationUnbindUserBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[CreateUserResult]:
    return await organization_unbind_users(
        client,
        user_ids=body.user_ids,
        organization_ids=body.organization_ids,
    )


@router.post(
    "/organizations/{org_id}/members",
    tags=["组织管理"],
    summary="获取组织成员列表",
    description="获取指定部门分支或企业机构下包含的成员，分页获取，支持关键字搜索、排序",
)
async def get_members_in_organization(
    body: OrganizationUserQueryBody,
    org_id: uuid.UUID,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                include_sub_members := <bool>$include_sub_members,
                organization := (
                    SELECT Organization FILTER .id = <uuid>$org_id
                ),
                users := (
                    SELECT (
                        organization.users
                        IF include_sub_members ELSE
                        organization.directly_users
                    ) FILTER (
                        true IF not EXISTS q ELSE
                        .name ?? '' ILIKE q OR
                        .username ?? '' ILIKE q OR
                        .mobile ?? '' ILIKE q OR
                        .email ?? '' ILIKE q
                    )
                ),
                total := count(users)
            SELECT (
                total := total,
                per_page := per_page,
                page := page,
                last := math::ceil(total / per_page),
                rows := array_agg((
                    SELECT users {{
                        id,
                        name,
                        username,
                        email,
                        mobile,
                        org_type: {{ id, code, name }},
                        departments := (
                            SELECT .directly_organizations {{
                                id,
                                code,
                                name
                            }}
                        ),
                        roles: {{ id, code, name }},
                        is_deleted,
                        created_at,
                        last_login_at
                    }}
                    ORDER BY {body.ordering_expr}
                    OFFSET (page - 1) * per_page
                    LIMIT per_page
                ))
            );\
            """,
        q=f"%{body.q}%" if body.q else None,
        page=body.page,
        per_page=body.per_page,
        include_sub_members=body.include_sub_members,
        org_id=org_id,
    )
    return PaginatedData.parse_raw(result)
