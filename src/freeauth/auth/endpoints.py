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
    GetUserByAccountResult,
    SendCodeResult,
    SignInResult,
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
    client: edgedb.AsyncIOClient,
    account: str,
    verify_type: AuthVerifyType,
    ttl: int | None,
    max_attempts: int | None,
    attempts_ttl: int | None,
) -> SendCodeResult:
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = AuthCodeType.SMS

    config = get_config()
    if account in config.demo_accounts:
        code = config.demo_code
    else:
        code = gen_random_string(6, letters=string.digits)

    logger.info(
        "Send %s %s to account %s by %s",
        verify_type.value,
        code,
        account,
        code_type.value,
    )
    rv = await send_code(
        client,
        account=account,
        code_type=code_type.value,  # type: ignore
        verify_type=verify_type.value,  # type: ignore
        code=code,
        ttl=(ttl or config.verify_code_ttl) * 60,
        max_attempts=max_attempts,
        attempts_ttl=attempts_ttl,
    )
    if not rv:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code": "验证码获取次数超限，请稍后再次获取"},
        )

    # TODO: send sms or email
    return rv


async def validate_auth_code(
    client: edgedb.AsyncIOClient,
    account: str,
    verify_type: AuthVerifyType,
    code: str,
    max_attempts: int | None,
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
        max_attempts=max_attempts,
    )
    if rv.code_required:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code": "验证码错误或已失效，请重新获取"},
        )
    if not rv.code_found:
        err_msg = "验证码错误，请重新输入"
        if max_attempts and rv.incorrect_attempts >= max_attempts:
            err_msg = (
                "您输入的错误验证码次数过多，当前验证码已失效，请重新获取"
            )
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code": err_msg},
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
    tags=["认证相关"],
    summary="发送注册验证码",
    description="通过短信或邮件发送注册验证码",
    dependencies=[Depends(verify_new_account_when_send_code)],
)
async def send_signup_code(
    body: SignUpSendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> SendCodeResult:
    login_settings = get_login_settings()
    validate_limit = await login_settings.get(
        "signup_code_validating_limit", client
    )
    ttl = None
    if validate_limit and len(validate_limit) == 2:
        ttl = validate_limit[1]

    max_attempts = None
    attempts_ttl = None
    send_limit_enabled = await login_settings.get(
        "signup_code_sending_limit_enabled", client
    )
    if send_limit_enabled:
        limit = await login_settings.get("signup_code_sending_limit", client)
        if limit and len(limit) > 1:
            max_attempts = limit[0]
            attempts_ttl = limit[1]
    return await send_auth_code(
        client,
        body.account,
        AuthVerifyType.SIGNUP,
        ttl,
        max_attempts,
        attempts_ttl,
    )


@router.post(
    "/sign_up/verify",
    tags=["认证相关"],
    summary="使用验证码注册账号",
    description="通过手机号或邮箱注册账号",
    dependencies=[Depends(verify_account_when_sign_up)],
)
async def sign_up_with_code(
    body: SignUpBody,
    response: Response,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    client_info: dict = Depends(get_client_info),
) -> SignInResult | None:
    login_settings = get_login_settings()
    max_attempts = None
    limit_enabled: bool = await login_settings.get(
        "signup_code_validating_limit_enabled", client
    )
    if limit_enabled:
        limit = await login_settings.get(
            "signup_code_validating_limit", client
        )
        if limit and len(limit) > 1:
            max_attempts = limit[0]
    await validate_auth_code(
        client, body.account, AuthVerifyType.SIGNUP, body.code, max_attempts
    )
    code_type: AuthCodeType = body.code_type
    username: str = gen_random_string(8)
    password: str = gen_random_string(12, secret=True)
    client_info: str = json.dumps(client_info)
    user = await sign_up(
        client,
        name=username,
        username=username,
        mobile=body.account if code_type == AuthCodeType.SMS else None,
        email=body.account if code_type == AuthCodeType.EMAIL else None,
        hashed_password=get_password_hash(password),
        client_info=client_info,
    )
    token = await create_access_token(client, response, user.id)
    return await sign_in(
        client,
        id=user.id,
        access_token=token,
        client_info=client_info,
    )


@router.post(
    "/sign_in/code",
    tags=["认证相关"],
    summary="发送登录验证码",
    description="通过短信或邮件发送登录验证码",
    dependencies=[Depends(verify_account_when_send_code)],
)
async def send_signin_code(
    body: SignInSendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> SendCodeResult:
    login_settings = get_login_settings()
    limit = await login_settings.get("signin_code_validating_limit", client)
    ttl = None
    if limit and len(limit) == 2:
        ttl = limit[1]

    max_attempts = None
    attempts_ttl = None
    send_limit_enabled = await login_settings.get(
        "signin_code_sending_limit_enabled", client
    )
    if send_limit_enabled:
        limit = await login_settings.get("signin_code_sending_limit", client)
        if limit and len(limit) > 1:
            max_attempts = limit[0]
            attempts_ttl = limit[1]
    return await send_auth_code(
        client,
        body.account,
        AuthVerifyType.SIGNIN,
        ttl,
        max_attempts,
        attempts_ttl,
    )


@router.post(
    "/sign_in/verify",
    tags=["认证相关"],
    summary="使用验证码登录账号",
    description="通过手机号或邮箱及验证码登录账号",
)
async def sign_in_with_code(
    body: SignInCodeBody,
    response: Response,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    user: GetUserByAccountResult = Depends(
        verify_account_when_sign_in_with_code
    ),
    client_info: dict = Depends(get_client_info),
) -> SignInResult | None:
    login_settings = get_login_settings()
    max_attempts = None
    limit_enabled: bool = await login_settings.get(
        "signin_code_validating_limit_enabled", client
    )
    if limit_enabled:
        limit = await login_settings.get(
            "signin_code_validating_limit", client
        )
        if limit and len(limit) > 1:
            max_attempts = limit[0]
    await validate_auth_code(
        client, body.account, AuthVerifyType.SIGNIN, body.code, max_attempts
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
    tags=["认证相关"],
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
) -> SignInResult | None:
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
