from __future__ import annotations

from http import HTTPStatus

import edgedb
from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr, Field
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client
from ..queries.query_api import CreateUserResult, create_user
from ..utils import gen_random_string, get_password_hash

router = APIRouter(tags=["用户管理"])


class BodyConfig:
    anystr_strip_whitespace = True


@dataclass(config=BodyConfig)
class UserPostBody:
    name: str | None = Field(None, title="姓名", max_length=50)
    username: str | None = Field(None, title="用户名", max_length=50)
    email: EmailStr | None = Field(None, title="邮箱")
    mobile: str | None = Field(None, title="手机号", regex=r"^1[0-9]{10}$")


################################
# Create users
################################


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
            detail={
                "error": (
                    f"{field.title()} '{getattr(user, field)}' already exists."
                )
            },
        )
    return created_user
