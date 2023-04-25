from __future__ import annotations

import re
import string
from http import HTTPStatus

import edgedb
from fastapi import HTTPException

from .. import logger
from ..config import get_settings
from ..queries.query_api import (
    AuthCodeType,
    AuthVerifyType,
    SendCodeResult,
    ValidateCodeResult,
    send_code,
    validate_code,
)
from ..utils import MOBILE_REGEX, gen_random_string


class AuthBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "type_error.enum": "不是有效的枚举值",
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
    }


async def send_auth_code(
    client: edgedb.AsyncIOClient, account: str, verify_type: AuthVerifyType
) -> SendCodeResult:
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = AuthCodeType.SMS

    # TODO: validate code limit

    settings = get_settings()
    if account in settings.demo_accounts:
        code = settings.demo_code
    else:
        code = gen_random_string(6, letters=string.digits)
    rv = await send_code(
        client,
        account=account,
        code_type=code_type.value,  # type: ignore
        verify_type=verify_type.value,  # type: ignore
        code=code,
        ttl=settings.verify_code_ttl,
    )
    logger.info(
        "Send %s %s to account %s by %s",
        verify_type.value,
        code,
        account,
        code_type.value,
    )
    # TODO: send sms or email
    return rv


async def validate_auth_code(
    client: edgedb.AsyncIOClient,
    account: str,
    verify_type: AuthVerifyType,
    code: str,
):
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = AuthCodeType.SMS
    rv: ValidateCodeResult = await validate_code(
        client,
        account=account,
        code_type=code_type.value,  # type: ignore
        verify_type=verify_type.value,  # type: ignore
        code=code,
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
