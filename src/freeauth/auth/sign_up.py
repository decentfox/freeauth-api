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
    SendVerifyCodeResult,
    ValidateVerifyCodeResult,
    create_user,
    get_user_by_exclusive_field,
    send_verify_code,
    validate_verify_code,
)
from ..utils import MOBILE_REGEX, gen_random_string, get_password_hash
from . import router


class AuthBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "type_error.enum": "不是有效的枚举值",
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
    }


@dataclass(config=AuthBodyConfig)
class SendVerifyCodeBody:
    code_type: AuthCodeType = Field(..., title="验证码类型")
    account: str = Field(
        ...,
        title="注册账号",
        description="手机号或邮箱",
    )

    @validator("account")
    def validate_account(cls, v, values):
        code_type = values.get("code_type")
        if code_type == AuthCodeType.SMS:
            if not re.match(MOBILE_REGEX, v):
                raise ValueError("仅支持中国大陆11位手机号")
        elif code_type == AuthCodeType.EMAIL:
            try:
                EmailStr.validate(v)
            except ValueError:
                raise ValueError("邮箱格式有误")
        else:
            raise ValueError("手机号码或邮箱格式有误")
        return v


@dataclass(config=AuthBodyConfig)
class SignUpVerifyCodeBody(SendVerifyCodeBody):
    code: str = Field(
        ...,
        title="验证码",
        description="使用手机号或邮箱注册时，需提供验证码",
    )


async def verify_sign_up_account(
    account: str,
    code_type: AuthCodeType,
    client: edgedb.AsyncIOClient,
):
    user = await get_user_by_exclusive_field(
        client,
        id=None,
        username=None,
        mobile=account if code_type == AuthCodeType.SMS else None,
        email=account if code_type == AuthCodeType.EMAIL else None,
    )
    if user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": f"{account} 已被使用"},
        )


async def verify_account_when_send_code(
    body: SendVerifyCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    await verify_sign_up_account(body.account, body.code_type, client)


async def verify_account_when_sign_up(
    body: SignUpVerifyCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    await verify_sign_up_account(body.account, body.code_type, client)


@router.post(
    "/sign_up/code",
    status_code=HTTPStatus.OK,
    summary="发送注册验证码",
    description="通过短信或邮件发送注册验证码",
    dependencies=[Depends(verify_account_when_send_code)],
)
async def send_sign_up_verify_code(
    body: SendVerifyCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> SendVerifyCodeResult:
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, body.account):
        code_type = AuthCodeType.SMS

    # TODO: validate code limit

    settings = get_settings()
    if body.account in settings.demo_accounts:
        code = settings.demo_code
    else:
        code = gen_random_string(6, letters=string.digits)
    rv = await send_verify_code(
        client,
        account=body.account,
        code_type=code_type.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
        ttl=settings.verify_code_ttl,
    )
    logger.info("Send %s to account %s", code, body.account)
    # TODO: send sms
    return rv


@router.post(
    "/sign_up/verify",
    status_code=HTTPStatus.OK,
    summary="注册账号",
    description="通过手机号或邮箱注册账号",
    dependencies=[Depends(verify_account_when_sign_up)],
)
async def sign_up_with_code(
    body: SignUpVerifyCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult | None:
    rv: ValidateVerifyCodeResult = await validate_verify_code(
        client,
        account=body.account,
        code_type=body.code_type.value,  # type: ignore
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
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

    # sign up
    username: str = gen_random_string(8)
    password: str = gen_random_string(12, secret=True)
    user: CreateUserResult = await create_user(
        client,
        mobile=body.account if body.code_type == AuthCodeType.SMS else None,
        name=username,
        username=username,
        email=body.account if body.code_type == AuthCodeType.EMAIL else None,
        hashed_password=get_password_hash(password),
    )
    return user
