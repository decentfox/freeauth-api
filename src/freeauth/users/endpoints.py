from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import List

import edgedb
from fastapi import Depends, HTTPException

from .. import get_edgedb_client
from ..app import router
from ..dataclasses import PaginatedData
from ..query_api import (
    CreateUserResult,
    DeleteUserResult,
    GetUserByIdResult,
    UpdateUserStatusResult,
    create_user,
    delete_user,
    get_user_by_id,
    resign_user,
    update_user,
    update_user_organization,
    update_user_roles,
    update_user_status,
)
from ..utils import gen_random_string, get_password_hash
from .dataclasses import (
    UserDeleteBody,
    UserOrganizationBody,
    UserPostBody,
    UserPutBody,
    UserQueryBody,
    UserResignationBody,
    UserRoleBody,
    UserStatusBody,
)

FILTER_TYPE_MAPPING = {
    "last_login_at": "datetime",
    "created_at": "datetime",
    "is_deleted": "bool",
}


@router.post(
    "/users",
    status_code=HTTPStatus.CREATED,
    tags=["用户管理"],
    summary="创建用户",
    description="姓名（选填）；用户名 + 手机号 + 邮箱（三选一必填）",
)
async def post_user(
    user: UserPostBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult:
    username: str | None = user.username
    if not username:
        username = gen_random_string(8)
    password: str = user.password or gen_random_string(12, secret=True)
    try:
        created_user = await create_user(
            client,
            name=user.name or username,
            username=username,
            email=user.email,
            mobile=user.mobile,
            hashed_password=get_password_hash(password),
            organization_ids=user.organization_ids,
            org_type_id=user.org_type_id,
        )
    except edgedb.errors.ConstraintViolationError as e:
        field = str(e).split(" ")[0]
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={field: f"{getattr(user, field)} 已被使用"},
        )
    return created_user


@router.put(
    "/users/status",
    tags=["用户管理"],
    summary="变更用户状态",
    description="支持批量变更",
)
async def toggle_user_status(
    body: UserStatusBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    user_ids: List[uuid.UUID] = body.user_ids
    is_deleted: bool = body.is_deleted
    updated_users: List[UpdateUserStatusResult] = await update_user_status(
        client, user_ids=user_ids, is_deleted=is_deleted
    )
    return {"users": updated_users}


@router.delete(
    "/users", tags=["用户管理"], summary="删除用户", description="支持批量删除"
)
async def delete_users(
    body: UserDeleteBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    user_ids: List[uuid.UUID] = body.user_ids
    deleted_users: List[DeleteUserResult] = await delete_user(
        client, user_ids=user_ids
    )
    return {"users": deleted_users}


@router.put(
    "/users/{user_id}",
    tags=["用户管理"],
    summary="更新用户信息",
    description="更新指定用户的用户信息",
)
async def put_user(
    user_id: uuid.UUID,
    user: UserPutBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult:
    try:
        updated_user: CreateUserResult | None = await update_user(
            client,
            name=user.name,
            username=user.username,
            email=user.email,
            mobile=user.mobile,
            id=user_id,
        )
    except edgedb.errors.ConstraintViolationError as e:
        field = str(e).split(" ")[0]
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={field: f"{getattr(user, field)} 已被使用"},
        )
    if not updated_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="用户不存在"
        )
    return updated_user


@router.put(
    "/users/{user_id}/organizations",
    tags=["组织管理"],
    summary="变更部门",
    description="变更指定用户的直属部门或企业机构",
)
async def update_member_organizations(
    user_id: uuid.UUID,
    body: UserOrganizationBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult | None:
    user: CreateUserResult | None = await update_user_organization(
        client,
        id=user_id,
        organization_ids=body.organization_ids,
        org_type_id=body.org_type_id,
    )
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="用户不存在"
        )
    return user


@router.put(
    "/users/{user_id}/roles",
    tags=["角色管理"],
    summary="配置角色",
    description="给指定用户配置指定一个或多个角色，或清空",
)
async def update_member_roles(
    user_id: uuid.UUID,
    body: UserRoleBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult | None:
    user: CreateUserResult | None = await update_user_roles(
        client, id=user_id, role_ids=body.role_ids
    )
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="用户不存在"
        )
    return user


@router.post(
    "/users/resign",
    tags=["组织管理"],
    summary="办理离职",
    description="支持批量为多个成员办理离职",
)
async def resign_users(
    body: UserResignationBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[DeleteUserResult]:
    user_ids: List[uuid.UUID] = body.user_ids
    is_deleted: bool | None = body.is_deleted
    return await resign_user(client, user_ids=user_ids, is_deleted=is_deleted)


@router.get(
    "/users/{user_id}",
    tags=["用户管理"],
    summary="获取用户信息",
    description="获取指定用户的用户信息",
)
async def get_user(
    user_id: uuid.UUID,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> GetUserByIdResult:
    user: GetUserByIdResult | None = await get_user_by_id(client, id=user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="用户不存在"
        )
    return user


@router.post(
    "/users/query",
    tags=["用户管理"],
    summary="获取用户列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
)
async def query_users(
    body: UserQueryBody,
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
            include_unassigned_users := <bool>$include_unassigned_users,
            users := (
                SELECT User
                FILTER (
                    true IF not EXISTS q ELSE
                    .name ?? '' ILIKE q OR
                    .username ?? '' ILIKE q OR
                    .mobile ?? '' ILIKE q OR
                    .email ?? '' ILIKE q
                ) AND (
                    true IF include_unassigned_users ELSE
                    EXISTS .org_type
                ) AND (
                    true IF not EXISTS org_type_id ELSE
                    (
                        NOT EXISTS .org_type OR
                        .org_type.id ?= org_type_id
                    ) IF include_unassigned_users ELSE
                    .org_type.id = org_type_id
                ) AND {filtering_expr}
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
        org_type_id=body.org_type_id,
        include_unassigned_users=body.include_unassigned_users,
    )

    return PaginatedData.parse_raw(result)
