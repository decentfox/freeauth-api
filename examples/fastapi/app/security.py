from __future__ import annotations

import json
from http import HTTPStatus

from fastapi import Depends, HTTPException, Response
from freeauth.conf.settings import get_settings
from freeauth.db.auth.auth_qry_async_edgeql import (
    GetCurrentUserResult,
    GetUserByAccessTokenResult,
    SignInResult,
    ValidateAccountResult,
    sign_in,
    sign_out,
    update_pwd,
    validate_account,
)
from freeauth.ext.fastapi_ext.utils import get_client_info
from freeauth.security.utils import get_password_hash, verify_password
from pydantic import BaseModel

from .asgi import auth_app, router


class AuthenticateBody(BaseModel):
    account: str
    password: str


@router.post("/security/authenticate")
async def authenticate_with_password(
    body: AuthenticateBody,
    response: Response,
    client_info: dict = Depends(get_client_info),
) -> SignInResult | None:
    user: ValidateAccountResult | None = await validate_account(
        auth_app.db,
        username=body.account,
        mobile=body.account,
        email=body.account,
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Account not found"
        )
    elif user.is_deleted:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Account is disabled",
        )
    elif not (
        user.hashed_password
        and verify_password(body.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid Password",
        )

    token = await auth_app.create_access_token(response, user.id)
    return await sign_in(
        auth_app.db,
        id=user.id,
        access_token=token,
        client_info=json.dumps(client_info),
    )


class ChangePasswordBody(BaseModel):
    password: str


@router.post("/security/password")
async def change_password(
    body: ChangePasswordBody,
    client_info: dict = Depends(get_client_info),
    current_user: GetCurrentUserResult = Depends(auth_app.current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Account not found",
        )
    elif current_user.is_deleted:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Account is disabled"
        )
    await update_pwd(
        auth_app.db,
        id=current_user.id,
        hashed_password=get_password_hash(body.password),
        client_info=json.dumps(client_info),
    )
    return "ok"


@router.post("/security/logout")
async def logout(
    response: Response,
    token: GetUserByAccessTokenResult = Depends(auth_app.get_access_token),
) -> str:
    if not token:
        return "ok"

    await sign_out(auth_app.db, access_token=token.access_token)
    settings = get_settings()
    response.delete_cookie(
        key=settings.jwt_cookie_key,
        httponly=True,
        secure=settings.jwt_cookie_secure,
        samesite="strict",
    )
    return "ok"


@router.get("/security/me")
async def get_current_user_profile(
    current_user: GetCurrentUserResult = Depends(auth_app.current_user_or_401),
) -> GetCurrentUserResult:
    return current_user
