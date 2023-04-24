from __future__ import annotations

import re
import string
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException
from pydantic import EmailStr, Field, validator
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client, logger
from ..config import get_settings
from ..queries.query_api import (
    AuthCodeType,
    AuthVerifyType,
    CreateUserResult,
    SendCodeResult,
    ValidateCodeResult,
    get_user_by_account,
    send_code,
    sign_in,
    validate_code,
)
from ..utils import MOBILE_REGEX, gen_random_string, get_password_hash
from . import router


class AuthBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
    }


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
    body: SignInPwdBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> SendCodeResult:
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, body.account):
        code_type = AuthCodeType.SMS

    # TODO: validate code limit

    settings = get_settings()
    if body.account in settings.demo_accounts:
        code = settings.demo_code
    else:
        code = gen_random_string(6, letters=string.digits)
    rv = await send_code(
        client,
        account=body.account,
        code_type=code_type.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNIN.value,  # type: ignore
        code=code,
        ttl=settings.verify_code_ttl,
    )
    logger.info(
        "Send signin code %s to account %s by %s",
        code,
        body.account,
        code_type,
    )
    # TODO: send sms or email
    return rv


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
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, body.account):
        code_type = AuthCodeType.SMS
    rv: ValidateCodeResult = await validate_code(
        client,
        account=body.account,
        code_type=code_type.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNIN.value,  # type: ignore
        code=body.code,
    )
    if not rv.code_found:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code": "验证码错误，请重新输入"},
        )
    elif not rv.code_valid:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code": "验证码已失效，请重新获取"},
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
    return await sign_in(client, id=user.id)
