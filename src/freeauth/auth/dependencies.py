from __future__ import annotations

from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException, Request
from user_agents import parse as ua_parse  # type: ignore

from .. import get_edgedb_client
from ..query_api import GetUserByAccountResult, get_user_by_account
from .dataclasses import (
    SignInCodeBody,
    SignInPwdBody,
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
    account: str,
    client: edgedb.AsyncIOClient,
):
    user = await get_user_by_account(client, account=account)
    if user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "该账号已注册，请直接登录"},
        )


async def verify_new_account_when_send_code(
    body: SignUpSendCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    await verify_signup_account(body.account, client)


async def verify_account_when_sign_up(
    body: SignUpBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    await verify_signup_account(body.account, client)


async def get_signin_account(
    account: str,
    client: edgedb.AsyncIOClient,
) -> GetUserByAccountResult:
    user = await get_user_by_account(client, account=account)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"account": "账号未注册，请您确认登录名输入是否正确"},
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
    return await get_signin_account(body.account, client)


async def verify_account_when_sign_in_with_code(
    body: SignInCodeBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> GetUserByAccountResult:
    return await get_signin_account(body.account, client)


async def verify_account_when_sign_in_with_pwd(
    body: SignInPwdBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> GetUserByAccountResult:
    return await get_signin_account(body.account, client)
