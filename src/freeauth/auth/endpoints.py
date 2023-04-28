from __future__ import annotations

import json
import re
import string
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException, Response
from jose import jwt

from .. import get_edgedb_client, logger
from ..app import router
from ..config import get_config
from ..query_api import (
    AuthCodeType,
    AuthVerifyType,
    CreateUserResult,
    GetUserByAccountResult,
    SendCodeResult,
    ValidateCodeResult,
    send_code,
    sign_in,
    sign_up,
    validate_code,
)
from ..settings import get_login_settings
from ..utils import MOBILE_REGEX, gen_random_string, get_password_hash
from .dataclasses import (
    SignInCodeBody,
    SignInPwdBody,
    SignInSendCodeBody,
    SignUpBody,
    SignUpSendCodeBody,
)
from .dependencies import (
    get_client_info,
    verify_account_when_send_code,
    verify_account_when_sign_in_with_code,
    verify_account_when_sign_in_with_pwd,
    verify_account_when_sign_up,
    verify_new_account_when_send_code,
)


async def send_auth_code(
    client: edgedb.AsyncIOClient, account: str, verify_type: AuthVerifyType
) -> SendCodeResult:
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = AuthCodeType.SMS

    # TODO: validate code limit

    config = get_config()
    if account in config.demo_accounts:
        code = config.demo_code
    else:
        code = gen_random_string(6, letters=string.digits)
    rv = await send_code(
        client,
        account=account,
        code_type=code_type.value,  # type: ignore
        verify_type=verify_type.value,  # type: ignore
        code=code,
        ttl=config.verify_code_ttl,
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


async def create_access_token(
    client: edgedb.AsyncIOClient, response: Response, user_id: uuid.UUID
) -> str:
    now = datetime.utcnow()
    config = get_config()
    login_settings = get_login_settings()
    jwt_token_ttl = await login_settings.get("jwt_token_ttl", client)
    payload = {
        "sub": str(user_id),
        "exp": now + timedelta(minutes=jwt_token_ttl or config.jwt_token_ttl),
    }
    token = jwt.encode(
        payload, config.jwt_secret_key, algorithm=config.jwt_algorithm
    )
    response.set_cookie(
        key=config.jwt_cookie_key,
        value=token,
        httponly=True,
        max_age=jwt_token_ttl * 60 if jwt_token_ttl else None,
        samesite="strict",
    )
    return token


@router.post(
    "/sign_up/code",
    status_code=HTTPStatus.OK,
    summary="发送注册验证码",
    description="通过短信或邮件发送注册验证码",
    dependencies=[Depends(verify_new_account_when_send_code)],
)
async def send_signup_code(
    body: SignUpSendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> SendCodeResult:
    return await send_auth_code(client, body.account, AuthVerifyType.SIGNUP)


@router.post(
    "/sign_up/verify",
    status_code=HTTPStatus.OK,
    summary="使用验证码注册账号",
    description="通过手机号或邮箱注册账号",
    dependencies=[Depends(verify_account_when_sign_up)],
)
async def sign_up_with_code(
    body: SignUpBody,
    response: Response,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    client_info: dict = Depends(get_client_info),
) -> CreateUserResult | None:
    await validate_auth_code(
        client, body.account, AuthVerifyType.SIGNUP, body.code
    )
    code_type: AuthCodeType = body.code_type
    username: str = gen_random_string(8)
    password: str = gen_random_string(12, secret=True)
    user = await sign_up(
        client,
        name=username,
        username=username,
        mobile=body.account if code_type == AuthCodeType.SMS else None,
        email=body.account if code_type == AuthCodeType.EMAIL else None,
        hashed_password=get_password_hash(password),
        client_info=json.dumps(client_info),
    )
    token = await create_access_token(client, response, user.id)
    return await sign_in(
        client,
        id=user.id,
        access_token=token,
        client_info=json.dumps(client_info),
    )


@router.post(
    "/sign_in/code",
    status_code=HTTPStatus.OK,
    summary="发送登录验证码",
    description="通过短信或邮件发送登录验证码",
    dependencies=[Depends(verify_account_when_send_code)],
)
async def send_signin_code(
    body: SignInSendCodeBody,
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
    response: Response,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    user: CreateUserResult = Depends(verify_account_when_sign_in_with_code),
    client_info: dict = Depends(get_client_info),
) -> CreateUserResult | None:
    await validate_auth_code(
        client, body.account, AuthVerifyType.SIGNIN, body.code
    )
    token = await create_access_token(client, response, user.id)
    return await sign_in(
        client,
        id=user.id,
        access_token=token,
        client_info=json.dumps(client_info),
    )


@router.post(
    "/sign_in",
    status_code=HTTPStatus.OK,
    summary="使用密码登录账号",
    description="通过用户名或手机号或邮箱及密码登录账号",
)
async def sign_in_with_pwd(
    body: SignInPwdBody,
    response: Response,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    user: GetUserByAccountResult = Depends(
        verify_account_when_sign_in_with_pwd
    ),
    client_info: dict = Depends(get_client_info),
) -> CreateUserResult | None:
    if user.hashed_password != get_password_hash(body.password):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "密码输入错误"},
        )
    token = await create_access_token(client, response, user.id)
    return await sign_in(
        client,
        id=user.id,
        access_token=token,
        client_info=json.dumps(client_info),
    )
