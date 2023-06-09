from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import List

import edgedb
from fastapi import BackgroundTasks, Depends, HTTPException

from freeauth.db.admin.admin_qry_async_edgeql import (
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
from freeauth.security.utils import gen_random_string, get_password_hash

from ..app import auth_app, router
from ..dataclasses import PaginatedData, QueryBody
from ..tasks import send_email
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
    dependencies=[Depends(auth_app.perm_accepted("manage:users"))],
)
async def post_user(
    user: UserPostBody, background_tasks: BackgroundTasks
) -> CreateUserResult:
    username: str | None = user.username
    if not username:
        username = gen_random_string(8)
    password: str = user.password or gen_random_string(12, secret=True)
    try:
        created_user = await create_user(
            auth_app.db,
            name=user.name or username,
            username=username,
            email=user.email,
            mobile=user.mobile,
            hashed_password=get_password_hash(password),
            reset_pwd_on_first_login=user.reset_pwd_on_first_login,
            organization_ids=user.organization_ids,
            org_type_id=user.org_type_id,
        )
    except edgedb.errors.ConstraintViolationError as e:
        field = str(e).split(" ")[0]
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={field: f"{getattr(user, field)} 已被使用"},
        )
    if user.send_first_login_email and user.email:
        background_tasks.add_task(
            send_email,
            tpl="user_created.html",
            subject="账号已创建",
            to=user.email,
            body=dict(
                username=username,
                email=user.email,
                password=password,
            ),
        )
    return created_user


@router.put(
    "/users/status",
    tags=["用户管理"],
    summary="变更用户状态",
    description="支持批量变更",
    dependencies=[Depends(auth_app.perm_accepted("manage:users"))],
)
async def toggle_user_status(
    body: UserStatusBody,
):
    user_ids: List[uuid.UUID] = body.user_ids
    is_deleted: bool = body.is_deleted
    updated_users: List[UpdateUserStatusResult] = await update_user_status(
        auth_app.db, user_ids=user_ids, is_deleted=is_deleted
    )
    return {"users": updated_users}


@router.delete(
    "/users",
    tags=["用户管理"],
    summary="删除用户",
    description="支持批量删除",
    dependencies=[Depends(auth_app.perm_accepted("manage:users"))],
)
async def delete_users(
    body: UserDeleteBody,
):
    user_ids: List[uuid.UUID] = body.user_ids
    deleted_users: List[DeleteUserResult] = await delete_user(
        auth_app.db, user_ids=user_ids
    )
    return {"users": deleted_users}


@router.put(
    "/users/{user_id}",
    tags=["用户管理"],
    summary="更新用户信息",
    description="更新指定用户的用户信息",
    dependencies=[Depends(auth_app.perm_accepted("manage:users"))],
)
async def put_user(
    user_id: uuid.UUID,
    user: UserPutBody,
) -> CreateUserResult:
    try:
        updated_user: CreateUserResult | None = await update_user(
            auth_app.db,
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
    dependencies=[
        Depends(auth_app.perm_accepted("manage:users", "manage:orgs"))
    ],
)
async def update_member_organizations(
    user_id: uuid.UUID,
    body: UserOrganizationBody,
) -> CreateUserResult | None:
    user: CreateUserResult | None = await update_user_organization(
        auth_app.db,
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
    dependencies=[
        Depends(auth_app.perm_accepted("manage:users", "manage:roles"))
    ],
)
async def update_member_roles(
    user_id: uuid.UUID,
    body: UserRoleBody,
) -> CreateUserResult | None:
    user: CreateUserResult | None = await update_user_roles(
        auth_app.db, id=user_id, role_ids=body.role_ids
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
    dependencies=[
        Depends(auth_app.perm_accepted("manage:users", "manage:orgs"))
    ],
)
async def resign_users(
    body: UserResignationBody,
) -> list[DeleteUserResult]:
    user_ids: List[uuid.UUID] = body.user_ids
    is_deleted: bool | None = body.is_deleted
    return await resign_user(
        auth_app.db, user_ids=user_ids, is_deleted=is_deleted
    )


@router.get(
    "/users/{user_id}",
    tags=["用户管理"],
    summary="获取用户信息",
    description="获取指定用户的用户信息",
    dependencies=[Depends(auth_app.perm_accepted("manage:users"))],
)
async def get_user(
    user_id: uuid.UUID,
) -> GetUserByIdResult:
    user: GetUserByIdResult | None = await get_user_by_id(
        auth_app.db, id=user_id
    )
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
    dependencies=[
        Depends(
            auth_app.perm_accepted(
                "manage:users", "manage:roles", "manage:orgs"
            )
        )
    ],
)
async def query_users(
    body: UserQueryBody,
) -> PaginatedData:
    filtering_expr = body.get_filtering_expr(FILTER_TYPE_MAPPING)
    result = await auth_app.db.query_single_json(
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


@router.post(
    "/users/{user_id}/permissions",
    tags=["用户管理"],
    summary="获取指定用户的权限列表",
    description="获取指定用户的权限，分页获取，支持关键字搜索、排序及条件过滤",
    dependencies=[Depends(auth_app.perm_accepted("manage:users"))],
)
async def get_permissions_in_user(
    body: QueryBody,
    user_id: uuid.UUID,
) -> PaginatedData:
    result = await auth_app.db.query_single_json(
        f"""\
        with
            page := <optional int64>$page ?? 1,
            per_page := <optional int64>$per_page ?? 20,
            q := <optional str>$q,
            user := (
                select User filter .id = <uuid>$user_id
            ),
            permissions := (
                select (user.permissions)
                filter (
                    true if not exists q else
                    .name ?? '' ilike q or
                    .code ?? '' ilike q
                )
            ),
            total := count(permissions)
        select (
            total := total,
            per_page := per_page,
            page := page,
            last := math::ceil(total / per_page),
            rows := array_agg((
                select permissions {{
                    id,
                    name,
                    code,
                    description,
                    roles: {{ id, code, name }},
                    application: {{ name }},
                    tags: {{ name }},
                    is_deleted,
                }}
                order by {body.ordering_expr}
                offset (page - 1) * per_page
                limit per_page
            ))
        );\
        """,
        q=f"%{body.q}%" if body.q else None,
        page=body.page,
        per_page=body.per_page,
        user_id=user_id,
    )

    return PaginatedData.parse_raw(result)
