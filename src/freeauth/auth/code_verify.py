from __future__ import annotations

import re
import string
from http import HTTPStatus

import edgedb
from fastapi import APIRouter, Depends
from pydantic import EmailStr, Field, validator
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client, logger
from ..config import get_settings
from ..queries.query_api import (
    AuthCodeType,
    AuthVerifyType,
    SendVerifyCodeResult,
    send_verify_code,
)
from ..utils import MOBILE_REGEX, gen_random_string

router = APIRouter(tags=["认证相关"])


class AuthBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "type_error.enum": "不是有效的枚举值",
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
    }


@dataclass(config=AuthBodyConfig)
class VerifyRecordPostBody:
    account: str = Field(
        ...,
        title="手机号或邮箱",
        description="如使用短信验证则需提供手机号码，如使用邮件验证则需提供邮箱",
    )
    verify_type: AuthVerifyType = Field(
        ...,
        title="验证场景类型",
        description="登录或注册",
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
    "/verify_codes",
    status_code=HTTPStatus.CREATED,
    summary="发送验证码",
    description="通过短信或邮件发送验证码",
)
async def request_verify_code(
    body: VerifyRecordPostBody,
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
                verify_type=body.verify_type.value,  # type: ignore
                code=code,
                ttl=settings.verify_code_ttl,
            )
            logger.info("Send %s to account %s", code, body.account)
            return rv
        except edgedb.errors.ConstraintViolationError:
            pass
