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

import uuid
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException, Query

from freeauth.conf.settings import get_settings
from freeauth.db.admin.admin_qry_async_edgeql import (
    AddMissingPermissionsResult,
    CreatePermissionResult,
    CreatePermissionTagResult,
    CreateRoleResult,
    DeletePermissionTagResult,
    GetPermissionByIdOrCodeResult,
    GetPermissionByIdOrCodeResultTagsItem,
    QueryPermissionsResult,
    UpdatePermissionStatusResult,
    create_permission,
    create_permission_tag,
    delete_permission,
    delete_permission_tag,
    get_permission_by_id_or_code,
    perm_bind_roles,
    perm_unbind_roles,
    query_permission_tags,
    query_permissions,
    reorder_permission_tags,
    update_permission,
    update_permission_status,
    update_permission_tag,
)

from ..app import auth_app, router
from ..dataclasses import PaginatedData, QueryBody
from .dataclasses import (
    BasePermissionBody,
    PermissionDeleteBody,
    PermissionPutBody,
    PermissionStatusBody,
    PermissionTagDeleteBody,
    PermissionTagReorderBody,
    PermissionTagUpdateBody,
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
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def post_permission(
    body: BasePermissionBody,
) -> CreatePermissionResult:
    settings = get_settings()
    assert settings.freeauth_app_id
    try:
        permission = await create_permission(
            auth_app.db,
            name=body.name,
            code=body.code,
            description=body.description,
            application_id=settings.freeauth_app_id,
            tags=body.tags,
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
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def toggle_permissions_status(
    body: PermissionStatusBody,
) -> list[UpdatePermissionStatusResult]:
    return await update_permission_status(
        auth_app.db, ids=body.ids, is_deleted=body.is_deleted
    )


@router.delete(
    "/permissions",
    tags=["权限管理"],
    summary="删除权限",
    description="批量删除权限",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def delete_permissions(
    body: PermissionDeleteBody,
) -> list[AddMissingPermissionsResult]:
    return await delete_permission(auth_app.db, ids=body.ids)


@router.get(
    "/permissions/{id_or_code}",
    tags=["权限管理"],
    summary="获取权限信息",
    description="获取指定权限的信息",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def get_permission(
    id_or_code: uuid.UUID | str = Depends(parse_permission_id_or_code),
) -> GetPermissionByIdOrCodeResult:
    permission: GetPermissionByIdOrCodeResult | None = (
        await get_permission_by_id_or_code(
            auth_app.db,
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
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def put_permission(
    body: PermissionPutBody,
    id_or_code: uuid.UUID | str = Depends(parse_permission_id_or_code),
) -> CreatePermissionResult:
    try:
        permission: CreatePermissionResult | None = await update_permission(
            auth_app.db,
            name=body.name,
            code=body.code,
            description=body.description,
            tags=body.tags,
            is_deleted=body.is_deleted,
            id=id_or_code if isinstance(id_or_code, uuid.UUID) else None,
            current_code=(id_or_code if isinstance(id_or_code, str) else None),
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
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def get_permissions(
    body: QueryBody,
) -> PaginatedData:
    filtering_expr = body.get_filtering_expr(FILTER_TYPE_MAPPING)
    settings = get_settings()
    result = await auth_app.db.query_single_json(
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
                        roles: {{ id, name }},
                        application: {{ name, is_protected }},
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
        application_id=settings.freeauth_app_id,
    )
    return PaginatedData.parse_raw(result)


@router.post(
    "/permissions/bind_roles",
    tags=["权限管理"],
    summary="添加角色",
    description="关联一个或多个角色到权限",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def bind_roles_to_perm(
    body: PermRoleBody,
) -> list[CreateRoleResult]:
    return await perm_bind_roles(
        auth_app.db,
        permission_ids=body.permission_ids,
        role_ids=body.role_ids,
    )


@router.post(
    "/permissions/unbind_roles",
    tags=["权限管理"],
    summary="移除角色",
    description="将一个或多个角色的权限移除",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def unbind_roles_to_perm(
    body: PermRoleBody,
) -> list[CreateRoleResult]:
    return await perm_unbind_roles(
        auth_app.db,
        permission_ids=body.permission_ids,
        role_ids=body.role_ids,
    )


@router.post(
    "/permissions/{permission_id}/roles",
    tags=["权限管理"],
    summary="获取权限绑定角色列表",
    description="获取指定权限下绑定的角色，分页获取，支持关键字搜索、排序",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def get_roles_in_permission(
    body: QueryBody,
    permission_id: uuid.UUID,
) -> PaginatedData:
    result = await auth_app.db.query_single_json(
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
                        is_protected,
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
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def get_users_in_permission(
    body: QueryBody,
    permission_id: uuid.UUID,
) -> PaginatedData:
    result = await auth_app.db.query_single_json(
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
    description="获取权限相关的所有标签",
    dependencies=[
        Depends(auth_app.perm_accepted("manage:perms", "manage:roles"))
    ],
)
async def get_permission_tags() -> (
    dict[str, list[GetPermissionByIdOrCodeResultTagsItem]]
):
    permission_tags: list[GetPermissionByIdOrCodeResultTagsItem] = (
        await query_permission_tags(auth_app.db)
    )
    return {"permission_tags": permission_tags}


@router.get(
    "/permissions",
    tags=["权限管理"],
    summary="获取权限列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
    dependencies=[
        Depends(auth_app.perm_accepted("manage:perms", "manage:roles"))
    ],
)
async def query_permissions_filter_by_role(
    page: int | None = None,
    per_page: int | None = None,
    q: str | None = None,
    tag_ids: list[uuid.UUID] | None = Query(None),
    role_id: uuid.UUID | None = None,
) -> QueryPermissionsResult:
    settings = get_settings()
    return await query_permissions(
        auth_app.db,
        page=page,
        per_page=per_page,
        q=q,
        application_id=settings.freeauth_app_id,
        tag_ids=tag_ids,
        role_id=role_id,
    )


@router.post(
    "/permission_tags",
    status_code=HTTPStatus.CREATED,
    tags=["权限管理"],
    summary="创建权限标签",
    description="创建权限标签",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def post_permission_tag(
    body: PermissionTagUpdateBody,
) -> CreatePermissionTagResult:
    try:
        role = await create_permission_tag(
            auth_app.db,
            name=body.name,
        )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"name": f"{body.name} 已被使用"},
        )
    return role


@router.delete(
    "/permission_tags",
    tags=["权限管理"],
    summary="删除权限标签",
    description="批量删除权限标签",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def delete_permission_tags(
    body: PermissionTagDeleteBody,
) -> list[DeletePermissionTagResult]:
    return await delete_permission_tag(auth_app.db, ids=body.ids)


@router.put(
    "/permission_tags/{id}",
    tags=["权限管理"],
    summary="更新权限标签",
    description="更新指定权限标签的名称",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def put_permission_tag(
    body: PermissionTagUpdateBody,
    id: uuid.UUID,
) -> CreatePermissionTagResult:
    try:
        permission_tag: CreatePermissionTagResult | None = (
            await update_permission_tag(auth_app.db, name=body.name, id=id)
        )
        if not permission_tag:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="标签不存在"
            )
    except edgedb.errors.ConstraintViolationError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"name": f"{body.name} 已被使用"},
        )
    return permission_tag


@router.post(
    "/permission_tags/reorder",
    tags=["权限管理"],
    summary="更新权限标签排序",
    description="更新权限标签排序",
    dependencies=[Depends(auth_app.perm_accepted("manage:perms"))],
)
async def reorder_tags(
    body: PermissionTagReorderBody,
) -> list[CreatePermissionTagResult]:
    return await reorder_permission_tags(auth_app.db, ids=body.ids)
