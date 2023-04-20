from __future__ import annotations

import string
from http import HTTPStatus

import edgedb
from fastapi import APIRouter, Depends
from pydantic import Field
from pydantic.dataclasses import dataclass

from .. import get_edgedb_client
from ..queries.query_api import (
    CodeType,
    SendVerifyCodeResult,
    send_verify_code,
)
from ..utils import gen_random_string

router = APIRouter(tags=["认证相关"])


class AuthBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.email": "邮箱格式有误",
        "value_error.str.regex": "仅支持中国大陆11位手机号",
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
    code_type: CodeType = Field(
        ...,
        title="验证方式",
        description="短信验证或邮件验证",
    )


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
    while True:
        try:
            code: str = gen_random_string(6, letters=string.digits)
            return await send_verify_code(
                client,
                account=body.account,
                code_type=body.code_type.value,
                code=code,
            )
        except edgedb.errors.ConstraintViolationError:
            pass
