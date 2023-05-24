from __future__ import annotations

import uuid
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException

from freeauth.db.admin.admin_qry_async_edgeql import (
    CreatePermissionResult,
    CreateRoleResult,
    DeletePermissionResult,
    GetPermissionByIdOrCodeResult,
    GetPermissionByIdOrCodeResultTagsItem,
    UpdatePermissionStatusResult,
    create_permission,
    delete_permission,
    get_permission_by_id_or_code,
    perm_bind_roles,
    perm_unbind_roles,
    query_permission_tags,
    update_permission,
    update_permission_status,
)

from .. import get_edgedb_client
from ..app import router
from ..dataclasses import PaginatedData, QueryBody
from .dataclasses import (
    BasePermissionBody,
    PermissionDeleteBody,
    PermissionPutBody,
    PermissionQueryBody,
    PermissionStatusBody,
    PermRoleBody,
)
from .dependencies import parse_permission_id_or_code

FILTER_TYPE_MAPPING = {"created_at": "datetime", "is_deleted": "bool"}


@router.post(
    "/permissions",
    status_code=HTTPStatus.CREATED,
    tags=["权限管理"],
    summary="创建权限",
    description="创建新权限",
)
async def post_permission(
    body: BasePermissionBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreatePermissionResult:
    try:
        permission = await create_permission(
            client,
            name=body.name,
            code=body.code,
            description=body.description,
            application_id=body.application_id,
            new_tags=body.new_tags,
            existing_tag_ids=body.existing_tag_ids,
        )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return permission


@router.put(
    "/permissions/status",
    tags=["权限管理"],
    summary="变更权限状态",
    description="批量变更权限状态",
)
async def toggle_permissions_status(
    body: PermissionStatusBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[UpdatePermissionStatusResult]:
    return await update_permission_status(
        client, ids=body.ids, is_deleted=body.is_deleted
    )


@router.delete(
    "/permissions",
    tags=["权限管理"],
    summary="删除权限",
    description="批量删除权限",
)
async def delete_permissions(
    body: PermissionDeleteBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[DeletePermissionResult]:
    return await delete_permission(client, ids=body.ids)


@router.get(
    "/permissions/{id_or_code}",
    tags=["权限管理"],
    summary="获取权限信息",
    description="获取指定权限的信息",
)
async def get_permission(
    id_or_code: uuid.UUID | str = Depends(parse_permission_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> GetPermissionByIdOrCodeResult:
    permission: GetPermissionByIdOrCodeResult | None = (
        await get_permission_by_id_or_code(
            client,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            code=id_or_code if isinstance(id_or_code, str) else None,
        )
    )
    if not permission:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="权限不存在"
        )
    return permission


@router.put(
    "/permissions/{id_or_code}",
    tags=["权限管理"],
    summary="更新权限",
    description="更新指定权限的信息",
)
async def put_permission(
    body: PermissionPutBody,
    id_or_code: uuid.UUID | str = Depends(parse_permission_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> GetPermissionByIdOrCodeResult:
    try:
        permission: GetPermissionByIdOrCodeResult | None = (
            await update_permission(
                client,
                name=body.name,
                code=body.code,
                description=body.description,
                new_tags=body.new_tags,
                existing_tag_ids=body.existing_tag_ids,
                is_deleted=body.is_deleted,
                id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
                current_code=(
                    id_or_code if isinstance(id_or_code, str) else None
                ),
            )
        )
        if not permission:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="权限不存在"
            )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return permission


@router.post(
    "/permissions/query",
    tags=["权限管理"],
    summary="获取权限列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
)
async def get_permissions(
    body: PermissionQueryBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    filtering_expr = body.get_filtering_expr(FILTER_TYPE_MAPPING)
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                application_id := <optional uuid>$application_id,
                permissions := (
                    SELECT Permission
                    FILTER (
                        true IF not EXISTS q ELSE
                        .name ILIKE q OR
                        .code ?? '' ILIKE q OR
                        .description ?? '' ILIKE q
                    ) AND (
                        true IF not EXISTS application_id ELSE
                        .application.id = application_id
                    ) AND {filtering_expr}
                ),
                total := count(permissions)

            SELECT (
                total := total,
                per_page := per_page,
                page := page,
                last := math::ceil(total / per_page),
                rows := array_agg((
                    SELECT permissions {{
                        id,
                        name,
                        code,
                        description,
                        application: {{ name }},
                        tags: {{ name }},
                        is_deleted,
                        created_at
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
        application_id=body.application_id,
    )
    return PaginatedData.parse_raw(result)


@router.post(
    "/permissions/bind_roles",
    tags=["权限管理"],
    summary="添加角色",
    description="关联一个或多个角色到权限",
)
async def bind_roles_to_perm(
    body: PermRoleBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[CreateRoleResult]:
    return await perm_bind_roles(
        client, permission_ids=body.permission_ids, role_ids=body.role_ids
    )


@router.post(
    "/permissions/unbind_roles",
    tags=["权限管理"],
    summary="移除角色",
    description="将一个或多个角色的权限移除",
)
async def unbind_roles_to_perm(
    body: PermRoleBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[CreateRoleResult]:
    return await perm_unbind_roles(
        client, permission_ids=body.permission_ids, role_ids=body.role_ids
    )


@router.post(
    "/permissions/{permission_id}/roles",
    tags=["权限管理"],
    summary="获取权限绑定角色列表",
    description="获取指定权限下绑定的角色，分页获取，支持关键字搜索、排序",
)
async def get_roles_in_permission(
    body: QueryBody,
    permission_id: uuid.UUID,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                permission := (
                    SELECT Permission FILTER .id = <uuid>$permission_id
                ),
                roles := (
                    SELECT (
                        permission.roles
                    ) FILTER (
                        true IF not EXISTS q ELSE
                        .name ILIKE q OR
                        .code ?? '' ILIKE q OR
                        .description ?? '' ILIKE q
                    )
                ),
                total := count(roles)
            SELECT (
                total := total,
                per_page := per_page,
                page := page,
                last := math::ceil(total / per_page),
                rows := array_agg((
                    SELECT roles {{
                        id,
                        name,
                        code,
                        description,
                        org_type: {{
                            code,
                            name,
                        }},
                        is_deleted,
                        created_at
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
        permission_id=permission_id,
    )
    return PaginatedData.parse_raw(result)


@router.post(
    "/permissions/{permission_id}/users",
    tags=["权限管理"],
    summary="获取权限关联的用户列表",
    description="获取拥有指定权限的用户，分页获取，支持关键字搜索、排序",
)
async def get_users_in_permission(
    body: QueryBody,
    permission_id: uuid.UUID,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                permission := (
                    SELECT Permission FILTER .id = <uuid>$permission_id
                ),
                roles := (
                    SELECT permission.roles
                ),
                users := (
                    SELECT (
                        roles.users
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
                            SELECT .directly_organizations {{ id, code, name }}
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
        permission_id=permission_id,
    )
    return PaginatedData.parse_raw(result)


@router.get(
    "/permission_tags",
    tags=["权限管理"],
    summary="获取权限标签",
    description="获取指定权限的所有标签",
)
async def get_permission_tags(
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> dict[str, list[GetPermissionByIdOrCodeResultTagsItem]]:
    permission_tags: list[GetPermissionByIdOrCodeResultTagsItem] = (
        await query_permission_tags(client)
    )
    return {"permission_tags": permission_tags}
