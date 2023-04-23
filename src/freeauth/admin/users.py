from __future__ import annotations

import uuid
from enum import Enum
from http import HTTPStatus
from typing import Any, List

import edgedb
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, root_validator, validator
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client
from ..queries.query_api import (
    CreateUserResult,
    DeleteUserResult,
    UpdateUserStatusResult,
    create_user,
    delete_user,
    get_user_by_exclusive_field,
    update_user,
    update_user_status,
)
from ..utils import MOBILE_REGEX, gen_random_string, get_password_hash

router = APIRouter(tags=["用户管理"])

TYPE_MAPPING = {
    "str": "str",
    "int": "int64",
    "bool": "bool",
    "uuid.UUID": "uuid",
    "datetime.datetime": "datetime",
}


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
        regex=MOBILE_REGEX,
    )

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @root_validator
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


class FilterOperatorEnum(str, Enum):
    eq = "eq"
    neq = "neq"
    gt = "gt"
    gte = "gte"
    lt = "lt"
    lte = "lte"
    ct = "ct"
    nct = "nct"

    def __int__(self):
        self.expr = ""

    def format(self, *args: object, **kwargs: object) -> str:
        return self.expr.format(*args, **kwargs)


FilterOperatorEnum.eq.expr = "{0} = {1}"
FilterOperatorEnum.neq.expr = "({0} != {1}) ?? true"
FilterOperatorEnum.gt.expr = "{0} > {1}"
FilterOperatorEnum.gte.expr = "{0} >= {1}"
FilterOperatorEnum.lt.expr = "{0} < {1}"
FilterOperatorEnum.lte.expr = "{0} <= {1}"
FilterOperatorEnum.ct.expr = "contains({0}, {1})"
FilterOperatorEnum.nct.expr = "(NOT contains({0}, {1})) ?? true"


@dataclass
class FilterItem:
    field: str = Field(..., title="字段名")
    operator: FilterOperatorEnum = Field(
        ...,
        title="运算符",
    )
    value: Any = Field(..., title="值")


@dataclass(config=UserBodyConfig)
class UserQueryBody:
    q: str | None = Field(
        None,
        title="搜索关键字",
        description="支持搜索用户姓名、用户名、手机号、邮箱",
        example="张三",
    )
    order_by: List[str] | None = Field(
        None,
        title="排序字段",
        description=(
            "支持多个排序字段，需降序排列时在字段前加 '-' 前缀，例如"
            " '-created_at'"
        ),
        example='["username", "-created_at"]',
    )
    filter_by: List[FilterItem] | None = Field(
        None,
        title="筛选条件",
        description=(
            "支持多个筛选条件，每个筛选条件包含 field（字段名）, operator"
            ' （运算符）, value（值）三个数据，例如： {"field": "mobile",'
            ' "operator": "eq", "value": "13800000000"}。'
            "支持的运算符有：eq（等于）, neq（不等于）, gt（大于）,"
            " gte（大于等于）, lt（小于）, lte（小于等于）, ct（包含）,"
            " nct（不包含）"
        ),
        example=(
            '[{"field": "mobile", "operator": "eq", "value": "13800000000"}]'
        ),
    )
    page: int | None = Field(
        1, title="分页页码", description="起始页码默认为 1"
    )
    per_page: int | None = Field(
        20,
        title="分页大小",
        description="默认为 20，取值为 1~100",
        ge=1,
        le=100,
    )

    @property
    def ordering_expr(self) -> str:
        return (
            " then ".join(
                f".{field[1:]} desc" if field.startswith("-") else f".{field}"
                for field in self.order_by
            )
            if self.order_by
            else ".created_at desc"
        )

    @property
    def filtering_expr(self) -> str:
        if not self.filter_by:
            return "true"

        ret: list = []
        user_annotations = CreateUserResult.__dict__.get("__annotations__", {})
        for field in self.filter_by:
            val_type = TYPE_MAPPING[
                user_annotations[field.field].split(" | ")[0]
            ]
            ret.append(
                field.operator.format(
                    f".{field.field}", f"<{val_type}>'{field.value}'"
                )
            )
        return " and ".join(ret)


class PaginatedUsers(BaseModel):
    total: int = Field(..., title="用户总数量")
    rows: List[CreateUserResult] = Field(..., title="用户列表")
    per_page: int = Field(..., title="当前分页大小")
    page: int = Field(..., title="当前分页页码")
    last: int = Field(..., title="最后一页页码")


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
            detail={field: f"{getattr(user, field)} 已被使用"},
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
            detail={field: f"{getattr(user, field)} 已被使用"},
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
    user: CreateUserResult | None = await get_user_by_exclusive_field(
        client, id=user_id, username=None, mobile=None, email=None
    )
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="用户不存在"
        )
    return user


@router.post(
    "/users/query",
    summary="获取用户列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
)
async def query_users(
    body: UserQueryBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedUsers:
    result = await client.query_single_json(
        f"""\
        WITH
            page := <optional int64>$page ?? 1,
            per_page := <optional int64>$per_page ?? 20,
            q := <optional str>$q,
            users := (
                SELECT User
                FILTER (
                    true IF not EXISTS q ELSE
                    .name ?? '' ILIKE q OR
                    .username ?? '' ILIKE q OR
                    .mobile ?? '' ILIKE q OR
                    .email ?? '' ILIKE q
                ) AND {body.filtering_expr}
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
    )

    return PaginatedUsers.parse_raw(result)
