from __future__ import annotations

from http import HTTPStatus

import edgedb
from edgedb.asyncio_client import AsyncIOIteration
from fastapi import Depends, HTTPException, Request
from jose import ExpiredSignatureError, JWTError, jwt

from . import get_edgedb_client, logger
from .config import get_config
from .query_api import CreateUserResult, get_user_by_access_token


class AccessTokenError(Exception):
    pass


async def get_current_user(
    req: Request, client: edgedb.AsyncIOClient = Depends(get_edgedb_client)
) -> CreateUserResult:
    try:
        config = get_config()
        token = req.cookies.get(config.jwt_cookie_key)
        if not token:
            raise AccessTokenError("missing token")

        try:
            payload = jwt.decode(
                token, config.jwt_secret_key, algorithms=[config.jwt_algorithm]
            )
        except ExpiredSignatureError:
            raise AccessTokenError("token expired")
        except JWTError:
            raise AccessTokenError("invalid token")
        else:
            user: CreateUserResult | None = await get_user_by_access_token(
                client, access_token=token
            )
            if not user:
                raise AccessTokenError("token not found")

            user_id = payload.get("sub")
            if user_id != str(user.id):
                raise AccessTokenError("user mismatches in token")

            if user.is_deleted:
                raise AccessTokenError("user disabled")
    except AccessTokenError as e:
        logger.info(e)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="身份验证失败"
        )

    if isinstance(client, AsyncIOIteration):
        client._client.with_globals({"current_user_id": user.id})
    else:
        client.with_globals({"current_user_id": user.id})
    return user
