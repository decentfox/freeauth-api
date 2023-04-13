from __future__ import annotations

from http import HTTPStatus

import edgedb
from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr, Field, root_validator
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client
from ..queries.query_api import CreateUserResult, create_user
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
    }


@dataclass(config=UserBodyConfig)
class UserPostBody:
    name: str | None = Field(None, title="姓名", max_length=50)
    username: str | None = Field(None, title="用户名", max_length=50)
    email: EmailStr | None = Field(None, title="邮箱")
    mobile: str | None = Field(None, title="手机号", regex=r"^1[0-9]{10}$")

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


@router.post("/users", status_code=HTTPStatus.CREATED)
async def post_user(
    user: UserPostBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult:
    username = user.username
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
            detail={"error": f'"{getattr(user, field)}" 已被使用'},
        )
    return created_user
