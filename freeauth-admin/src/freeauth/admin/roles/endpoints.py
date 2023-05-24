from __future__ import annotations

import uuid
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException

from freeauth.db.admin.admin_qry_async_edgeql import (
    CreateRoleResult,
    CreateUserResult,
    DeleteRoleResult,
    UpdateRoleStatusResult,
    create_role,
    delete_role,
    get_role_by_id_or_code,
    role_bind_users,
    role_unbind_users,
    update_role,
    update_role_status,
)

from .. import get_edgedb_client
from ..app import router
from ..dataclasses import PaginatedData, QueryBody
from .dataclasses import (
    RoleDeleteBody,
    RolePostBody,
    RolePutBody,
    RoleQueryBody,
    RoleStatusBody,
    RoleUserBody,
)
from .dependencies import parse_role_id_or_code

FILTER_TYPE_MAPPING = {"created_at": "datetime", "is_deleted": "bool"}


@router.post(
    "/roles",
    status_code=HTTPStatus.CREATED,
    tags=["角色管理"],
    summary="创建角色",
    description="创建新角色",
)
async def post_role(
    body: RolePostBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateRoleResult:
    try:
        role = await create_role(
            client,
            name=body.name,
            code=body.code,
            description=body.description,
            org_type_id=body.org_type_id,
        )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return role


@router.put(
    "/roles/status",
    tags=["角色管理"],
    summary="变更角色状态",
    description="批量变更角色状态",
)
async def toggle_roles_status(
    body: RoleStatusBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[UpdateRoleStatusResult]:
    return await update_role_status(
        client, ids=body.ids, is_deleted=body.is_deleted
    )


@router.delete(
    "/roles",
    tags=["角色管理"],
    summary="删除角色",
    description="批量删除角色",
)
async def delete_roles(
    body: RoleDeleteBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[DeleteRoleResult]:
    return await delete_role(client, ids=body.ids)


@router.get(
    "/roles/{id_or_code}",
    tags=["角色管理"],
    summary="获取角色信息",
    description="获取指定角色的信息",
)
async def get_role(
    id_or_code: uuid.UUID | str = Depends(parse_role_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateRoleResult:
    role: CreateRoleResult | None = await get_role_by_id_or_code(
        client,
        id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
        code=id_or_code if isinstance(id_or_code, str) else None,
    )
    if not role:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="角色不存在"
        )
    return role


@router.put(
    "/roles/{id_or_code}",
    tags=["角色管理"],
    summary="更新角色",
    description="更新指定角色的信息",
)
async def put_role(
    body: RolePutBody,
    id_or_code: uuid.UUID | str = Depends(parse_role_id_or_code),
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateRoleResult:
    try:
        role: CreateRoleResult | None = await update_role(
            client,
            name=body.name,
            code=body.code,
            description=body.description,
            is_deleted=body.is_deleted,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            current_code=id_or_code if isinstance(id_or_code, str) else None,
        )
        if not role:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="角色不存在"
            )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"code": f"{body.code} 已被使用"},
        )
    return role


@router.post(
    "/roles/query",
    tags=["角色管理"],
    summary="获取角色列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
)
async def get_roles(
    body: RoleQueryBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    filtering_expr = body.get_filtering_expr(FILTER_TYPE_MAPPING)
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                org_type_id := <optional uuid>$org_type_id,
                include_global_roles := <bool>$include_global_roles,
                include_org_type_roles := <bool>$include_org_type_roles,
                roles := (
                    SELECT Role
                    FILTER (
                        true IF not EXISTS q ELSE
                        .name ILIKE q OR
                        .code ?? '' ILIKE q OR
                        .description ?? '' ILIKE q OR
                        .org_type.name ?? '' ILIKE q
                    ) AND (
                        true IF include_global_roles ELSE
                        EXISTS .org_type
                    ) AND (
                        true IF include_org_type_roles ELSE
                        NOT EXISTS .org_type
                    ) AND (
                        true IF not EXISTS org_type_id ELSE
                        (
                            NOT EXISTS .org_type OR
                            .org_type.id ?= org_type_id
                        ) IF include_global_roles ELSE
                        .org_type.id = org_type_id
                    ) AND {filtering_expr}
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
                            id,
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
        org_type_id=body.org_type_id,
        include_global_roles=body.include_global_roles,
        include_org_type_roles=body.include_org_type_roles,
    )
    return PaginatedData.parse_raw(result)


@router.post(
    "/roles/{role_id}/users",
    tags=["角色管理"],
    summary="获取角色绑定用户列表",
    description="获取指定角色下绑定的用户，分页获取，支持关键字搜索、排序",
)
async def get_users_in_role(
    body: QueryBody,
    role_id: uuid.UUID,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    result = await client.query_single_json(
        f"""\
            WITH
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                role := (
                    SELECT Role FILTER .id = <uuid>$role_id
                ),
                users := (
                    SELECT (
                        role.users
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
        role_id=role_id,
    )
    return PaginatedData.parse_raw(result)


@router.post(
    "/roles/bind_users",
    tags=["角色管理"],
    summary="添加用户",
    description="关联一个或多个用户到角色",
)
async def bind_users_to_roles(
    body: RoleUserBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[CreateUserResult]:
    return await role_bind_users(
        client, user_ids=body.user_ids, role_ids=body.role_ids
    )


@router.post(
    "/roles/unbind_users",
    tags=["角色管理"],
    summary="移除用户",
    description="将一个或多个用户的角色移除",
)
async def unbind_roles_from_users(
    body: RoleUserBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[CreateUserResult]:
    return await role_unbind_users(
        client, user_ids=body.user_ids, role_ids=body.role_ids
    )
