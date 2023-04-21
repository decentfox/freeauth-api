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
    SendVerifyCodeResult,
    ValidateVerifyCodeResult,
    send_verify_code,
    validate_verify_code,
)
from ..utils import MOBILE_REGEX, gen_random_string
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
    account: str = Field(
        ...,
        title="手机号或邮箱",
        description="如使用短信验证则需提供手机号码，如使用邮件验证则需提供邮箱",
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
class SignUpVerifyCodeBody:
    code_type: AuthCodeType = Field(..., title="验证码类型")
    account: str = Field(
        ...,
        title="注册账号",
        description="手机号或邮箱",
    )
    code: str = Field(
        ...,
        title="验证码",
        description="使用手机号或邮箱注册时，需提供验证码",
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
class SignUpBody:
    account: str = Field(
        ...,
        title="用户名、手机号或邮箱",
        description="注册账号",
    )
    code: str | None = Field(
        None,
        title="验证码",
        description="使用手机号或邮箱注册时，需提供验证码",
    )
    code_type: AuthCodeType | None = Field(None, title="验证码类型")
    password: str | None = Field(
        None,
        title="登录密码",
        description="使用用户名注册时，需提供登录密码",
    )

    @validator("account")
    def validate_account(cls, v):
        if not re.match(MOBILE_REGEX, v):
            try:
                EmailStr.validate(v)
            except ValueError:
                raise ValueError("手机号码或邮箱格式有误")
        return v


@router.post(
    "/sign_up/code",
    status_code=HTTPStatus.OK,
    summary="发送注册验证码",
    description="通过短信或邮件发送注册验证码",
)
async def send_sign_up_verify_code(
    body: SendVerifyCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> SendVerifyCodeResult:
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, body.account):
        code_type = AuthCodeType.SMS
    settings = get_settings()
    while True:
        try:
            code: str = gen_random_string(6, letters=string.digits)
            rv = await send_verify_code(
                client,
                account=body.account,
                code_type=code_type.value,  # type: ignore
                verify_type=AuthVerifyType.SIGNUP.value,  # type: ignore
                code=code,
                ttl=settings.verify_code_ttl,
            )
            logger.info("Send %s to account %s", code, body.account)
            return rv
        except edgedb.errors.ConstraintViolationError:
            pass


@router.post(
    "/sign_up/verify",
    status_code=HTTPStatus.OK,
    summary="注册账号",
    description="通过手机号或邮箱注册账号",
)
async def sign_up_with_code(
    body: SignUpVerifyCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> ValidateVerifyCodeResult | None:
    rv = await validate_verify_code(
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
    return rv
