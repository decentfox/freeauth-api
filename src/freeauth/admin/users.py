from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import List

import edgedb
from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr, Field, root_validator
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client
from ..queries.query_api import (
    CreateUserResult,
    DeleteUserResult,
    UpdateUserStatusResult,
    create_user,
    delete_user,
    get_user_by_id,
    update_user,
    update_user_status,
)
from ..utils import gen_random_string, get_password_hash

router = APIRouter(tags=["用户管理"])


class UserBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.any_str.max_length": (
            "最大支持的长度为{limit_value}个字符"
        ),
        "value_error.email": "邮箱格式有误",
        "value_error.str.regex": "仅支持中国大陆11位手机号",
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
        "type_error.uuid": "用户ID格式错误",
    }


@dataclass(config=UserBodyConfig)
class UserPostBody:
    name: str | None = Field(
        None,
        title="姓名",
        description="用户姓名（选填），默认为用户名",
        max_length=50,
    )
    username: str | None = Field(
        None,
        title="用户名",
        description="登录用户名，未提供则由随机生成",
        max_length=50,
    )
    email: EmailStr | None = Field(
        None, description="邮箱，可接收登录验证邮件", title="邮箱"
    )
    mobile: str | None = Field(
        None,
        title="手机号",
        description="仅支持中国大陆11位手机号码，可接收短信验证邮件",
        regex=r"^1[0-9]{10}$",
    )

    @root_validator(skip_on_failure=True)
    def validate_username_or_email_or_mobile(cls, values):
        username, email, mobile = (
            values.get("username"),
            values.get("email"),
            values.get("mobile"),
        )
        if not (username or email or mobile):
            raise ValueError("用户名、邮箱、手机号三个信息中请至少提供一项")
        return values


@dataclass(config=UserBodyConfig)
class UserPutBody:
    name: str = Field(
        ...,
        title="姓名",
        description="用户姓名",
        max_length=50,
    )
    username: str = Field(
        ...,
        title="用户名",
        description="登录用户名",
        max_length=50,
    )
    email: EmailStr | None = Field(
        None, description="邮箱，可接收登录验证邮件", title="邮箱"
    )
    mobile: str | None = Field(
        None,
        title="手机号",
        description="仅支持中国大陆11位手机号码，可接收短信验证邮件",
        regex=r"^1[0-9]{10}$",
    )


@dataclass(config=UserBodyConfig)
class UserStatusBody:
    user_ids: List[uuid.UUID] = Field(
        ...,
        title="用户 ID 数组",
        description="待变更状态的用户 ID 列表",
    )
    is_deleted: bool = Field(
        ...,
        title="是否禁用",
        description="true 为禁用用户，false 为启用用户",
    )


@dataclass(config=UserBodyConfig)
class UserDeleteBody:
    user_ids: List[uuid.UUID] = Field(
        ...,
        title="用户 ID 数组",
        description="待删除的用户 ID 列表",
    )


@router.post(
    "/users",
    status_code=HTTPStatus.CREATED,
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
    password: str = gen_random_string(12, secret=True)
    try:
        created_user = await create_user(
            client,
            name=user.name or username,
            username=username,
            email=user.email,
            mobile=user.mobile,
            hashed_password=get_password_hash(password),
        )
    except edgedb.errors.ConstraintViolationError as e:
        field = str(e).split(" ")[0]
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=[
                {"loc": [field], "msg": f'"{getattr(user, field)}" 已被使用'}
            ],
        )
    return created_user


@router.put(
    "/users/status", summary="变更用户状态", description="支持批量变更"
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


@router.delete("/users", summary="删除用户", description="支持批量删除")
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
    summary="更新用户信息",
    description="更新指定用户的用户信息",
)
async def put_user(
    user_id: uuid.UUID,
    user: UserPutBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    try:
        updated_user = await update_user(
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
            detail=[
                {"loc": [field], "msg": f'"{getattr(user, field)}" 已被使用'}
            ],
        )
    return updated_user


@router.get(
    "/users/{user_id}",
    summary="获取用户信息",
    description="获取指定用户的用户信息",
)
async def get_user(
    user_id: uuid.UUID,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    user: CreateUserResult | None = await get_user_by_id(client, id=user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="用户不存在"
        )
    return user
