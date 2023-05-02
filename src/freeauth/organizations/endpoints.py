from __future__ import annotations

import uuid
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException

from .. import get_edgedb_client
from ..app import router
from ..dataclasses import PaginatedData, QueryBody
from ..query_api import (
    CreateEnterpriseResult,
    CreateOrgTypeResult,
    DeleteEnterpriseResult,
    DeleteOrgTypeResult,
    UpdateOrgTypeStatusResult,
    create_enterprise,
    create_org_type,
    delete_enterprise,
    delete_org_type,
    get_enterprise_by_id_or_code,
    get_org_type_by_id,
    query_org_types,
    update_enterprise,
    update_org_type,
    update_org_type_status,
)
from .dataclasses import (
    EnterpriseDeleteBody,
    EnterprisePostBody,
    EnterprisePutBody,
    OrgTypeDeleteBody,
    OrgTypePostBody,
    OrgTypePutBody,
    OrgTypeStatusBody,
)
from .dependencies import parse_id_or_code


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
    "/org_types/{org_type_id}",
    tags=["组织管理"],
    summary="获取组织类型信息",
    description="获取指定组织类型的信息",
)
async def get_org_type(
    org_type_id: uuid.UUID,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateOrgTypeResult:
    org_type: CreateOrgTypeResult | None = await get_org_type_by_id(
        client, id=org_type_id
    )
    if not org_type:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="组织类型不存在"
        )
    return org_type


@router.put(
    "/org_types/{org_type_id}",
    tags=["组织管理"],
    summary="更新组织类型",
    description="更新指定组织类型的信息",
)
async def put_org_type(
    org_type_id: uuid.UUID,
    body: OrgTypePutBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateOrgTypeResult:
    try:
        org_type: CreateOrgTypeResult | None = await update_org_type(
            client,
            name=body.name,
            code=body.code,
            description=body.description,
            is_deleted=body.is_deleted,
            id=org_type_id,
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
    id_or_code: str | uuid.UUID = Depends(parse_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateEnterpriseResult:
    try:
        enterprise: CreateEnterpriseResult | None = await update_enterprise(
            client,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            current_code=id_or_code if isinstance(id_or_code, str) else None,
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
    "/enterprises",
    tags=["组织管理"],
    summary="删除企业机构",
    description="批量删除企业机构",
)
async def delete_enterprises(
    body: EnterpriseDeleteBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> dict[str, list[DeleteEnterpriseResult]]:
    deleted_enterprises: list[DeleteEnterpriseResult] = (
        await delete_enterprise(client, ids=body.ids)
    )
    return {"enterprises": deleted_enterprises}


@router.get(
    "/enterprises/{id_or_code}",
    tags=["组织管理"],
    summary="获取企业机构信息",
    description="通过企业机构 ID 或 Code，获取指定企业机构的信息",
)
async def get_enterprise(
    id_or_code: str | uuid.UUID = Depends(parse_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateEnterpriseResult:
    enterprise: CreateEnterpriseResult | None = (
        await get_enterprise_by_id_or_code(
            client,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            code=id_or_code if isinstance(id_or_code, str) else None,
        )
    )
    if not enterprise:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="企业机构不存在"
        )
    return enterprise


@router.post(
    "/org_types/{org_type_id}/enterprises/query",
    tags=["组织管理"],
    summary="获取指定组织类型下的企业机构列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
)
async def get_enterprises_in_org_type(
    org_type_id: uuid.UUID,
    body: QueryBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
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
                    ) AND .org_type.id = <uuid>'{org_type_id}'
                ),
                total := count(enterprises)

            SELECT (
                total := total,
                per_page := per_page,
                page := page,
                last := math::ceil(total / per_page),
                rows := array_agg((
                    SELECT enterprises {{
                        name,
                        code,
                        tax_id,
                        issuing_bank,
                        bank_account_number,
                        contact_address,
                        contact_phone_num
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
    )
    return PaginatedData.parse_raw(result)
