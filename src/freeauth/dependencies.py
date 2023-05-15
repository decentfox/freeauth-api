from __future__ import annotations

from http import HTTPStatus

import edgedb
from edgedb.asyncio_client import AsyncIOIteration
from fastapi import Depends, HTTPException, Request
from jose import ExpiredSignatureError, JWTError, jwt

from . import get_edgedb_client, logger
from .config import get_config
from .query_api import CreateUserResult, get_user_by_access_token


def get_access_token(req: Request):
    config = get_config()
    return req.cookies.get(config.jwt_cookie_key)


async def get_current_user(
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    access_token: str = Depends(get_access_token),
) -> CreateUserResult | None:
    config = get_config()
    if not access_token:
        logger.info("missing token")
        return None

    try:
        payload = jwt.decode(
            access_token,
            config.jwt_secret_key,
            algorithms=[config.jwt_algorithm],
        )
    except ExpiredSignatureError:
        logger.info("token expired")
        return None
    except JWTError:
        logger.info("invalid token")
        return None
    else:
        user: CreateUserResult | None = await get_user_by_access_token(
            client, access_token=access_token
        )
        if not user:
            logger.info("token not found")
            return None

        user_id = payload.get("sub")
        if user_id != str(user.id):
            logger.info("user mismatches in token")
            return None

        if user.is_deleted:
            logger.info("user disabled")
            return None

    if isinstance(client, AsyncIOIteration):
        client._client.with_globals({"current_user_id": user.id})
    else:
        client.with_globals({"current_user_id": user.id})
    return user


async def require_user(
    current_user: CreateUserResult | None = Depends(get_current_user),
) -> CreateUserResult:
    if current_user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="身份验证失败"
        )

    return current_user
