from __future__ import annotations

import re
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException
from pydantic import EmailStr, Field, validator
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client
from ..queries.query_api import (
    AuthVerifyType,
    CreateUserResult,
    SendCodeResult,
    get_user_by_account,
    sign_in,
)
from ..utils import MOBILE_REGEX, get_password_hash
from . import router
from .common import AuthBodyConfig, send_auth_code, validate_auth_code


@dataclass(config=AuthBodyConfig)
class SendCodeBody:
    account: str = Field(
        ...,
        title="登录账号",
        description="手机号或邮箱",
    )

    @validator("account")
    def validate_account(cls, v):
        if not re.match(MOBILE_REGEX, v):
            try:
                EmailStr.validate(v)
            except ValueError:
                raise ValueError("手机号码或邮箱格式有误")
        return v


@dataclass(config=AuthBodyConfig)
class SignInCodeBody(SendCodeBody):
    code: str = Field(
        ...,
        title="登录验证码",
        description="通过短信或邮件发送的登录验证码",
    )


@dataclass(config=AuthBodyConfig)
class SignInPwdBody:
    account: str = Field(
        ...,
        title="登录账号",
        description="用户名或手机号或邮箱",
    )
    password: str = Field(
        ...,
        title="登录密码",
        description="登录密码",
    )


async def get_signin_account(
    account: str,
    client: edgedb.AsyncIOClient,
    password: str | None = None,
) -> CreateUserResult:
    user = await get_user_by_account(
        client,
        account=account,
        hashed_password=get_password_hash(password) if password else None,
    )
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "账号未注册，请您确认登录名输入是否正确"},
        )
    if user.is_deleted:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "您的账号已停用"},
        )
    return user


async def verify_account_when_send_code(
    body: SendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult:
    return await get_signin_account(body.account, client)


async def verify_account_when_sign_in_with_code(
    body: SignInCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult:
    return await get_signin_account(body.account, client)


async def verify_account_when_sign_in_with_pwd(
    body: SignInPwdBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult:
    return await get_signin_account(
        body.account, client, password=body.password
    )


@router.post(
    "/sign_in/code",
    status_code=HTTPStatus.OK,
    summary="发送登录验证码",
    description="通过短信或邮件发送登录验证码",
    dependencies=[Depends(verify_account_when_send_code)],
)
async def send_signin_code(
    body: SendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> SendCodeResult:
    return await send_auth_code(client, body.account, AuthVerifyType.SIGNIN)


@router.post(
    "/sign_in/verify",
    status_code=HTTPStatus.OK,
    summary="使用验证码登录账号",
    description="通过手机号或邮箱及验证码登录账号",
)
async def sign_in_with_code(
    body: SignInCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    user: CreateUserResult = Depends(verify_account_when_sign_in_with_code),
) -> CreateUserResult | None:
    await validate_auth_code(
        client, body.account, AuthVerifyType.SIGNIN, body.code
    )
    return await sign_in(client, id=user.id)


@router.post(
    "/sign_in",
    status_code=HTTPStatus.OK,
    summary="使用密码登录账号",
    description="通过用户名或手机号或邮箱及密码登录账号",
)
async def sign_in_with_pwd(
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    user: CreateUserResult = Depends(verify_account_when_sign_in_with_pwd),
) -> CreateUserResult | None:
    user = await sign_in(client, id=user.id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "密码输入错误"},
        )
    return user
