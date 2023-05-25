from __future__ import annotations

import json
import re
import string
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus

from fastapi import Depends, HTTPException, Response
from jose import jwt

from freeauth.conf.settings import get_settings
from freeauth.db.auth.auth_qry_async_edgeql import (
    AuthAuditEventType,
    AuthAuditStatusCode,
    AuthCodeType,
    AuthVerifyType,
    GetUserByAccessTokenResult,
    GetUserByAccountResult,
    SendCodeResult,
    ValidateCodeResult,
    ValidatePwdResult,
    create_audit_log,
    send_code,
    sign_in,
    sign_out,
    sign_up,
    validate_code,
    validate_pwd,
)

from .. import logger
from ..app import auth_app, router
from ..audit_logs.dataclasses import AUDIT_STATUS_CODE_MAPPING
from ..settings import get_login_settings
from ..utils import (
    MOBILE_REGEX,
    gen_random_string,
    get_password_hash,
    verify_password,
)
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
    verify_account_when_sign_up,
    verify_new_account_when_send_code,
)


async def send_auth_code(
    account: str,
    verify_type: AuthVerifyType,
    ttl: int | None,
    max_attempts: int | None,
    attempts_ttl: int | None,
) -> SendCodeResult:
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = AuthCodeType.SMS

    settings = get_settings()
    if account in settings.demo_accounts:
        code = settings.demo_code
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
        auth_app.db,
        account=account,
        code_type=code_type.value,  # type: ignore
        verify_type=verify_type.value,  # type: ignore
        code=code,
        ttl=(ttl or settings.verify_code_ttl) * 60,
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
    account: str,
    verify_type: AuthVerifyType,
    code: str,
    max_attempts: int | None,
    user: GetUserByAccountResult | None,
    client_info: dict,
):
    code_type = AuthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = AuthCodeType.SMS
    rv: ValidateCodeResult = await validate_code(
        auth_app.db,
        account=account,
        code_type=code_type.value,  # type: ignore
        verify_type=verify_type.value,  # type: ignore
        code=code,
        max_attempts=max_attempts,
    )
    status_code = AuthAuditStatusCode(str(rv.status_code))
    if status_code != AuthAuditStatusCode.OK:
        if user:
            await create_audit_log(
                auth_app.db,
                user_id=user.id,
                client_info=json.dumps(client_info),
                status_code=status_code.value,  # type: ignore
                event_type=AuthAuditEventType.SIGNIN.value,  # type: ignore
            )
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code": AUDIT_STATUS_CODE_MAPPING[status_code]},
        )


async def create_access_token(response: Response, user_id: uuid.UUID) -> str:
    now = datetime.utcnow()
    settings = get_settings()
    login_settings = get_login_settings()
    jwt_token_ttl = await login_settings.get("jwt_token_ttl", auth_app.db)
    payload = {
        "sub": str(user_id),
        "exp": now + timedelta(
            minutes=jwt_token_ttl or settings.jwt_token_ttl
        ),
    }
    token = jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    response.set_cookie(
        key=settings.jwt_cookie_key,
        value=token,
        httponly=True,
        secure=settings.jwt_cookie_secure,
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
) -> SendCodeResult:
    settings = await get_login_settings().get_all(auth_app.db)
    sending_limit_enabled = settings["signup_code_sending_limit_enabled"]
    return await send_auth_code(
        account=body.account,
        verify_type=AuthVerifyType.SIGNUP,
        ttl=(
            settings["signup_code_validating_interval"]
            if settings["signup_code_validating_limit_enabled"]
            else None
        ),
        max_attempts=(
            settings["signup_code_sending_max_attempts"]
            if sending_limit_enabled
            else None
        ),
        attempts_ttl=(
            settings["signup_code_sending_interval"]
            if sending_limit_enabled
            else None
        ),
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
    client_info: dict = Depends(get_client_info),
) -> GetUserByAccessTokenResult | None:
    settings = await get_login_settings().get_all(auth_app.db)
    await validate_auth_code(
        account=body.account,
        verify_type=AuthVerifyType.SIGNUP,
        code=body.code,
        max_attempts=(
            settings["signup_code_validating_max_attempts"]
            if settings["signup_code_validating_limit_enabled"]
            else None
        ),
        user=None,
        client_info=client_info,
    )
    code_type: AuthCodeType = body.code_type
    username: str = gen_random_string(8)
    password: str = gen_random_string(12, secret=True)
    client_info: str = json.dumps(client_info)
    user = await sign_up(
        auth_app.db,
        name=username,
        username=username,
        mobile=body.account if code_type == AuthCodeType.SMS else None,
        email=body.account if code_type == AuthCodeType.EMAIL else None,
        hashed_password=get_password_hash(password),
        client_info=client_info,
    )
    token = await create_access_token(response, user.id)
    return await sign_in(
        auth_app.db,
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
) -> SendCodeResult:
    settings = await get_login_settings().get_all(auth_app.db)
    sending_limit_enabled = settings["signin_code_sending_limit_enabled"]
    return await send_auth_code(
        account=body.account,
        verify_type=AuthVerifyType.SIGNIN,
        ttl=(
            settings["signin_code_validating_interval"]
            if settings["signin_code_validating_limit_enabled"]
            else None
        ),
        max_attempts=(
            settings["signin_code_sending_max_attempts"]
            if sending_limit_enabled
            else None
        ),
        attempts_ttl=(
            settings["signin_code_sending_interval"]
            if sending_limit_enabled
            else None
        ),
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
    user: GetUserByAccountResult = Depends(
        verify_account_when_sign_in_with_code
    ),
    client_info: dict = Depends(get_client_info),
) -> GetUserByAccessTokenResult | None:
    settings = await get_login_settings().get_all(auth_app.db)
    await validate_auth_code(
        account=body.account,
        verify_type=AuthVerifyType.SIGNIN,
        code=body.code,
        max_attempts=(
            settings["signin_code_validating_max_attempts"]
            if settings["signin_code_validating_limit_enabled"]
            else None
        ),
        user=user,
        client_info=client_info,
    )
    token = await create_access_token(response, user.id)
    return await sign_in(
        auth_app.db,
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
    client_info: dict = Depends(get_client_info),
) -> GetUserByAccessTokenResult | None:
    settings = await get_login_settings().get_all(auth_app.db)
    pwd_signin_modes = settings["pwd_signin_modes"]
    if not pwd_signin_modes:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "系统不支持密码登录，请使用其他登录方式"},
        )
    user: ValidatePwdResult | None = await validate_pwd(
        auth_app.db,
        username=body.account if "username" in pwd_signin_modes else None,
        mobile=body.account if "mobile" in pwd_signin_modes else None,
        email=body.account if "email" in pwd_signin_modes else None,
        interval=(
            settings["signin_pwd_validating_interval"]
            if settings["signin_pwd_validating_limit_enabled"]
            else None
        ),
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail={
                "account": AUDIT_STATUS_CODE_MAPPING[
                    AuthAuditStatusCode.ACCOUNT_NOT_EXISTS
                ]
            },
        )
    field = "account"
    status_code: AuthAuditStatusCode | None = None
    if user.is_deleted:
        status_code = AuthAuditStatusCode.ACCOUNT_DISABLED
    elif not (
        user.hashed_password
        and verify_password(body.password, user.hashed_password)
    ):
        field = "password"
        status_code = AuthAuditStatusCode.INVALID_PASSWORD
        if (
            settings["signin_pwd_validating_limit_enabled"]
            and user.recent_failed_attempts
            >= settings["signin_pwd_validating_max_attempts"]
        ):
            status_code = AuthAuditStatusCode.PASSWORD_ATTEMPTS_EXCEEDED

    if status_code:
        await create_audit_log(
            auth_app.db,
            user_id=user.id,
            client_info=json.dumps(client_info),
            status_code=status_code.value,  # type: ignore
            event_type=AuthAuditEventType.SIGNIN.value,  # type: ignore
        )
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={field: AUDIT_STATUS_CODE_MAPPING[status_code]},
        )

    token = await create_access_token(response, user.id)
    return await sign_in(
        auth_app.db,
        id=user.id,
        access_token=token,
        client_info=json.dumps(client_info),
    )


@router.post(
    "/sign_out",
    tags=["认证相关"],
    summary="退出登录",
    description="清除用户登录态",
)
async def post_sign_out(
    response: Response,
    access_token: str = Depends(auth_app.get_access_token),
) -> str:
    if not access_token:
        return "ok"

    await sign_out(auth_app.db, access_token=access_token)
    settings = get_settings()
    response.delete_cookie(
        key=settings.jwt_cookie_key,
        httponly=True,
        secure=settings.jwt_cookie_secure,
        samesite="strict",
    )
    return "ok"


@router.get(
    "/me",
    tags=["认证相关"],
    summary="获取个人信息",
    description="获取当前登录用户的个人信息",
)
async def get_user_me(
    current_user: GetUserByAccessTokenResult = Depends(
        auth_app.get_current_user()
    ),
) -> GetUserByAccessTokenResult:
    if current_user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="身份验证失败"
        )
    return current_user