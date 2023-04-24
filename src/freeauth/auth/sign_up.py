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
    sign_up,
    validate_code,
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
class SendCodeBody:
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
class SignUpBody(SendCodeBody):
    code: str = Field(
        ...,
        title="注册验证码",
        description="通过短信或邮件发送的注册验证码",
    )


async def verify_signup_account(
    account: str,
    client: edgedb.AsyncIOClient,
):
    user = await get_user_by_account(
        client, account=account, hashed_password=None
    )
    if user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "该账号已注册，请直接登录"},
        )


async def verify_account_when_send_code(
    body: SendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    await verify_signup_account(body.account, client)


async def verify_account_when_sign_up(
    body: SignUpBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    await verify_signup_account(body.account, client)


@router.post(
    "/sign_up/code",
    status_code=HTTPStatus.OK,
    summary="发送注册验证码",
    description="通过短信或邮件发送注册验证码",
    dependencies=[Depends(verify_account_when_send_code)],
)
async def send_signup_code(
    body: SendCodeBody,
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
        verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
        code=code,
        ttl=settings.verify_code_ttl,
    )
    logger.info(
        "Send signup %s to account %s by %s", code, body.account, code_type
    )
    # TODO: send sms or email
    return rv


@router.post(
    "/sign_up/verify",
    status_code=HTTPStatus.OK,
    summary="使用验证码注册账号",
    description="通过手机号或邮箱注册账号",
    dependencies=[Depends(verify_account_when_sign_up)],
)
async def sign_up_with_code(
    body: SignUpBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateUserResult | None:
    code_type: AuthCodeType = body.code_type
    rv: ValidateCodeResult = await validate_code(
        client,
        account=body.account,
        code_type=code_type.value,  # type: ignore
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
    return await sign_up(
        client,
        name=username,
        username=username,
        mobile=body.account if code_type == AuthCodeType.SMS else None,
        email=body.account if code_type == AuthCodeType.EMAIL else None,
        hashed_password=get_password_hash(password),
    )
