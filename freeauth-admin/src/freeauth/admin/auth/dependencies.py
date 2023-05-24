from __future__ import annotations

import re
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException, Request
from user_agents import parse as ua_parse  # type: ignore

from freeauth.db.auth.auth_qry_async_edgeql import (
    AuthCodeType,
    GetUserByAccountResult,
    get_user_by_account,
)

from .. import get_edgedb_client
from ..settings import get_login_settings
from ..utils import MOBILE_REGEX
from .dataclasses import (
    SignInCodeBody,
    SignInSendCodeBody,
    SignUpBody,
    SignUpSendCodeBody,
)


def get_client_info(request: Request) -> dict:
    raw_ua: str | None = request.headers.get("User-Agent")
    user_agent = dict(
        raw_ua=raw_ua,
    )
    if raw_ua:
        ua = ua_parse(raw_ua)
        user_agent.update(
            os=ua.os.family,
            device=ua.device.family,
            browser=ua.browser.family,
        )
    return {
        "client_ip": request.headers.get(
            "X-Forwarded-For", request.client.host if request.client else None
        ),
        "user_agent": user_agent,
    }


async def verify_signup_account(
    client: edgedb.AsyncIOClient,
    username: str | None = None,
    mobile: str | None = None,
    email: str | None = None,
):
    user = await get_user_by_account(
        client, username=username, mobile=mobile, email=email
    )
    if user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "该账号已注册，请直接登录"},
        )


async def verify_new_account_when_send_code(
    body: SignUpSendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    login_settings = get_login_settings()
    signup_modes = await login_settings.get("signup_modes", client)
    if not signup_modes:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code_type": "系统不支持注册，如您已有账号，请直接登录"},
        )
    if body.code_type == AuthCodeType.SMS and "mobile" not in signup_modes:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code_type": "不支持手机号和验证码注册"},
        )
    if body.code_type == AuthCodeType.EMAIL and "email" not in signup_modes:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"code_type": "不支持邮箱和验证码注册"},
        )
    await verify_signup_account(
        client,
        mobile=body.account if body.code_type == AuthCodeType.SMS else None,
        email=body.account if body.code_type == AuthCodeType.EMAIL else None,
    )


async def verify_account_when_sign_up(
    body: SignUpBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    await verify_signup_account(
        client,
        mobile=body.account if body.code_type == AuthCodeType.SMS else None,
        email=body.account if body.code_type == AuthCodeType.EMAIL else None,
    )


async def get_signin_account(
    client: edgedb.AsyncIOClient,
    username: str | None = None,
    mobile: str | None = None,
    email: str | None = None,
) -> GetUserByAccountResult:
    user = await get_user_by_account(
        client, username=username, mobile=mobile, email=email
    )
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "账号不存在，请您确认登录信息输入是否正确"},
        )
    if user.is_deleted:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "您的账号已停用"},
        )
    return user


async def verify_account_when_send_code(
    body: SignInSendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> GetUserByAccountResult:
    login_settings = get_login_settings()
    code_signin_modes = await login_settings.get("code_signin_modes", client)
    if not code_signin_modes:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "系统不支持验证码登录，请使用其他登录方式"},
        )
    is_sms = re.match(MOBILE_REGEX, body.account)
    if is_sms:
        if "mobile" not in code_signin_modes:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail={"account": "不支持手机号和验证码登录"},
            )
    elif "email" not in code_signin_modes:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "不支持邮箱和验证码登录"},
        )
    return await get_signin_account(
        client,
        mobile=body.account if is_sms else None,
        email=body.account if not is_sms else None,
    )


async def verify_account_when_sign_in_with_code(
    body: SignInCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> GetUserByAccountResult:
    is_sms = re.match(MOBILE_REGEX, body.account)
    return await get_signin_account(
        client,
        mobile=body.account if is_sms else None,
        email=body.account if not is_sms else None,
    )
