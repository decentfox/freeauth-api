from __future__ import annotations

import uuid
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException

from .. import get_edgedb_client
from ..app import router
from ..query_api import (
    CreateOrgTypeResult,
    DeleteOrgTypeResult,
    UpdateOrgTypeStatusResult,
    create_org_type,
    delete_org_type,
    get_org_type_by_id,
    query_org_types,
    update_org_type,
    update_org_type_status,
)
from .dataclasses import (
    OrgTypeDeleteBody,
    OrgTypePostBody,
    OrgTypePutBody,
    OrgTypeStatusBody,
)

FILTER_TYPE_MAPPING = {
    "last_login_at": "datetime",
    "created_at": "datetime",
    "is_deleted": "bool",
}


@router.post(
    "/org_types",
    status_code=HTTPStatus.CREATED,
    tags=["组织管理"],
    summary="创建组织类型",
    description="包含字段：名称（必填）、描述（选填）",
)
async def post_org_type(
    body: OrgTypePostBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateOrgTypeResult:
    return await create_org_type(
        client,
        name=body.name,
        description=body.description,
    )


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
    description="获取指定用户的用户信息",
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
    org_type: CreateOrgTypeResult | None = await update_org_type(
        client,
        name=body.name,
        description=body.description,
        is_deleted=body.is_deleted,
        id=org_type_id,
    )
    if not org_type:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="组织类型不存在"
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
