from __future__ import annotations

import json
import re
import string
from http import HTTPStatus

from fastapi import Depends, HTTPException, Response

from freeauth.conf.login_settings import LoginSettings
from freeauth.conf.settings import get_settings
from freeauth.db.auth.auth_qry_async_edgeql import (
    FreeauthAuditEventType,
    FreeauthAuditStatusCode,
    FreeauthCodeType,
    FreeauthVerifyType,
    GetCurrentUserResult,
    GetUserByAccessTokenResult,
    GetUserByAccountResult,
    SendCodeResult,
    SignInResult,
    ValidateCodeResult,
    ValidatePwdResult,
    create_audit_log,
    send_code,
    sign_in,
    sign_out,
    sign_up,
    update_profile,
    update_pwd,
    validate_code,
    validate_pwd,
)
from freeauth.ext.fastapi_ext.utils import get_client_info
from freeauth.security.utils import (
    MOBILE_REGEX,
    gen_random_string,
    get_password_hash,
    verify_password,
)

from .. import logger
from ..app import auth_app, router
from ..audit_logs.dataclasses import AUDIT_STATUS_CODE_MAPPING
from .dataclasses import (
    ResetPwdBody,
    SignInCodeBody,
    SignInPwdBody,
    SignInSendCodeBody,
    SignUpBody,
    SignUpSendCodeBody,
    UpdateProfileBody,
)
from .dependencies import (
    verify_account_when_send_code,
    verify_account_when_sign_in_with_code,
    verify_account_when_sign_up,
    verify_new_account_when_send_code,
)


async def send_auth_code(
    account: str,
    verify_type: FreeauthVerifyType,
    ttl: int | None,
    max_attempts: int | None,
    attempts_ttl: int | None,
) -> SendCodeResult:
    code_type = FreeauthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = FreeauthCodeType.SMS

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
        code_type=code_type,
        verify_type=verify_type,
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
    verify_type: FreeauthVerifyType,
    code: str,
    max_attempts: int | None,
    user: GetUserByAccountResult | None,
    client_info: dict,
):
    code_type = FreeauthCodeType.EMAIL
    if re.match(MOBILE_REGEX, account):
        code_type = FreeauthCodeType.SMS
    rv: ValidateCodeResult = await validate_code(
        auth_app.db,
        account=account,
        code_type=code_type,
        verify_type=verify_type,
        code=code,
        max_attempts=max_attempts,
    )
    status_code = FreeauthAuditStatusCode(str(rv.status_code))
    if status_code != FreeauthAuditStatusCode.OK:
        if user:
            await create_audit_log(
                auth_app.db,
                user_id=user.id,
                client_info=json.dumps(client_info),
                status_code=status_code,
                event_type=FreeauthAuditEventType.SIGNIN,
            )
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code": AUDIT_STATUS_CODE_MAPPING[status_code]},
        )


@router.post(
    "/sign_up/code",
    tags=["认证相关"],
    summary="发送注册验证码",
    description="通过短信或邮件发送注册验证码",
    dependencies=[Depends(verify_new_account_when_send_code)],
)
async def send_signup_code(
    body: SignUpSendCodeBody,
    settings: LoginSettings = Depends(auth_app.login_settings),
) -> SendCodeResult:
    sending_limit_enabled = settings.signup_code_sending_limit_enabled
    return await send_auth_code(
        account=body.account,
        verify_type=FreeauthVerifyType.SIGNUP,
        ttl=(
            settings.signup_code_validating_interval
            if settings.signup_code_validating_limit_enabled
            else None
        ),
        max_attempts=(
            settings.signup_code_sending_max_attempts
            if sending_limit_enabled
            else None
        ),
        attempts_ttl=(
            settings.signup_code_sending_interval
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
    settings: LoginSettings = Depends(auth_app.login_settings),
) -> SignInResult | None:
    await validate_auth_code(
        account=body.account,
        verify_type=FreeauthVerifyType.SIGNUP,
        code=body.code,
        max_attempts=(
            settings.signup_code_validating_max_attempts
            if settings.signup_code_validating_limit_enabled
            else None
        ),
        user=None,
        client_info=client_info,
    )
    code_type: FreeauthCodeType = body.code_type
    username: str = gen_random_string(8)
    password: str = gen_random_string(12, secret=True)
    client_info: str = json.dumps(client_info)
    user = await sign_up(
        auth_app.db,
        name=username,
        username=username,
        mobile=body.account if code_type == FreeauthCodeType.SMS else None,
        email=body.account if code_type == FreeauthCodeType.EMAIL else None,
        hashed_password=get_password_hash(password),
        reset_pwd_on_next_login=settings.change_pwd_after_first_login_enabled,
        client_info=client_info,
    )
    token = await auth_app.create_access_token(response, user.id)
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
    settings: LoginSettings = Depends(auth_app.login_settings),
) -> SendCodeResult:
    sending_limit_enabled = settings.signin_code_sending_limit_enabled
    return await send_auth_code(
        account=body.account,
        verify_type=FreeauthVerifyType.SIGNIN,
        ttl=(
            settings.signin_code_validating_interval
            if settings.signin_code_validating_limit_enabled
            else None
        ),
        max_attempts=(
            settings.signin_code_sending_max_attempts
            if sending_limit_enabled
            else None
        ),
        attempts_ttl=(
            settings.signin_code_sending_interval
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
    settings: LoginSettings = Depends(auth_app.login_settings),
) -> SignInResult | None:
    await validate_auth_code(
        account=body.account,
        verify_type=FreeauthVerifyType.SIGNIN,
        code=body.code,
        max_attempts=(
            settings.signin_code_validating_max_attempts
            if settings.signin_code_validating_limit_enabled
            else None
        ),
        user=user,
        client_info=client_info,
    )
    token = await auth_app.create_access_token(response, user.id)
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
    settings: LoginSettings = Depends(auth_app.login_settings),
) -> SignInResult | None:
    pwd_signin_modes = settings.pwd_signin_modes
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
            settings.signin_pwd_validating_interval
            if settings.signin_pwd_validating_limit_enabled
            else None
        ),
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail={
                "account": AUDIT_STATUS_CODE_MAPPING[
                    FreeauthAuditStatusCode.ACCOUNT_NOT_EXISTS
                ]
            },
        )
    field = "account"
    status_code: FreeauthAuditStatusCode | None = None
    if user.is_deleted:
        status_code = FreeauthAuditStatusCode.ACCOUNT_DISABLED
    elif not (
        user.hashed_password
        and verify_password(body.password, user.hashed_password)
    ):
        field = "password"
        status_code = FreeauthAuditStatusCode.INVALID_PASSWORD
        if (
            settings.signin_pwd_validating_limit_enabled
            and user.recent_failed_attempts
            >= settings.signin_pwd_validating_max_attempts
        ):
            status_code = FreeauthAuditStatusCode.PASSWORD_ATTEMPTS_EXCEEDED

    if status_code:
        await create_audit_log(
            auth_app.db,
            user_id=user.id,
            client_info=json.dumps(client_info),
            status_code=status_code,
            event_type=FreeauthAuditEventType.SIGNIN,
        )
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={field: AUDIT_STATUS_CODE_MAPPING[status_code]},
        )

    token = await auth_app.create_access_token(response, user.id)
    return await sign_in(
        auth_app.db,
        id=user.id,
        access_token=token,
        client_info=json.dumps(client_info),
    )


@router.post(
    "/change_pwd",
    tags=["认证相关"],
    summary="重置密码",
    description="重置当前用户的登录密码",
)
async def change_password(
    body: ResetPwdBody,
    client_info: dict = Depends(get_client_info),
    current_user: GetCurrentUserResult = Depends(auth_app.current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="账号不存在"
        )
    if current_user.is_deleted:
        await create_audit_log(
            auth_app.db,
            user_id=current_user.id,
            client_info=json.dumps(client_info),
            status_code=FreeauthAuditStatusCode.ACCOUNT_DISABLED,
            event_type=FreeauthAuditEventType.CHANGEPWD,
        )
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="您的账号已停用"
        )
    await update_pwd(
        auth_app.db,
        id=current_user.id,
        hashed_password=get_password_hash(body.password),
        client_info=json.dumps(client_info),
    )
    return "ok"


@router.post(
    "/update_profile",
    tags=["认证相关"],
    summary="更新个人信息",
    description="更新当前用户的个人信息",
)
async def update_my_profile(
    body: UpdateProfileBody,
    current_user: GetCurrentUserResult = Depends(auth_app.current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="账号不存在"
        )
    if current_user.is_deleted:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="您的账号已停用"
        )
    await update_profile(
        auth_app.db,
        id=current_user.id,
        name=body.name,
        username=body.username,
        email=body.email,
        mobile=body.mobile,
    )
    return "ok"


@router.post(
    "/sign_out",
    tags=["认证相关"],
    summary="退出登录",
    description="清除用户登录态",
)
async def post_sign_out(
    response: Response,
    client_info: dict = Depends(get_client_info),
    token: GetUserByAccessTokenResult = Depends(auth_app.get_access_token),
    current_user: GetCurrentUserResult = Depends(auth_app.current_user),
) -> str:
    if not token:
        return "ok"

    await sign_out(auth_app.db, access_token=token.access_token)
    if current_user:
        await create_audit_log(
            auth_app.db,
            user_id=current_user.id,
            client_info=json.dumps(client_info),
            status_code=FreeauthAuditStatusCode.OK,
            event_type=FreeauthAuditEventType.SIGNOUT,
        )
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
    current_user: GetCurrentUserResult = Depends(auth_app.current_user_or_401),
) -> GetCurrentUserResult:
    return current_user
