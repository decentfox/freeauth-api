from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import Callable

import edgedb
from fastapi import Depends, FastAPI, HTTPException, Request
from jose import ExpiredSignatureError, JWTError, jwt

from freeauth.conf.login_settings import LoginSettings
from freeauth.conf.settings import get_settings
from freeauth.db.auth.auth_qry_async_edgeql import (
    GetUserByAccessTokenResult,
    get_login_setting,
    get_user_by_access_token,
)

logger = logging.getLogger(__name__)

__all__ = ["FreeAuthApp"]


class FreeAuthApp:
    """FreeAuth FastAPI extension.

    :param app: The FastAPI application to extend
    """

    def __init__(self, app: FastAPI | None = None):
        self.app: FastAPI | None = None
        self._edgedb_client: edgedb.AsyncIOClient | None = None
        self.settings = get_settings()

        if app is not None:
            self.init_app(app)

    def init_app(self, app: FastAPI) -> None:
        self.app = app

        self.app.add_event_handler("startup", self.setup_edgedb)
        self.app.add_event_handler("shutdown", self.shutdown_edgedb)

    async def setup_edgedb(self) -> None:
        self.db = edgedb.create_async_client(
            dsn=self.settings.edgedb_dsn or self.settings.edgedb_instance,
            database=self.settings.edgedb_database,
        )
        await self.db.ensure_connected()

    async def shutdown_edgedb(self) -> None:
        await self.db.aclose()

    @property
    def db(self) -> edgedb.AsyncIOClient:
        if not self._edgedb_client:
            raise RuntimeError("Can't find edgedb client")
        return self._edgedb_client

    @db.setter
    def db(self, client):
        self._edgedb_client = client

    def get_access_token(self, request: Request) -> str | None:
        access_token: str | None = request.cookies.get(
            self.settings.jwt_cookie_key
        )
        return access_token

    @property
    def current_user(self) -> Callable:
        async def dependency(
            access_token: str = Depends(self.get_access_token),
        ) -> GetUserByAccessTokenResult | None:
            if not access_token:
                logger.info("missing token")
                return None

            try:
                payload = jwt.decode(
                    access_token,
                    self.settings.jwt_secret_key,
                    algorithms=[self.settings.jwt_algorithm],
                )
            except ExpiredSignatureError:
                logger.info("token expired")
                return None
            except JWTError:
                logger.info("invalid token")
                return None
            else:
                user: GetUserByAccessTokenResult | None = (
                    await get_user_by_access_token(
                        self.db, access_token=access_token
                    )
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

            if self._edgedb_client:
                self._edgedb_client.with_globals({"current_user_id": user.id})
            return user

        return dependency

    @property
    def current_user_or_401(self) -> Callable:
        async def dependency(
            current_user: GetUserByAccessTokenResult
            | None = Depends(self.current_user),
        ) -> GetUserByAccessTokenResult:
            if not current_user:
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED, detail="身份验证失败"
                )
            return current_user

        return dependency

    async def get_login_settings(self) -> LoginSettings:
        settings = LoginSettings()
        fields = settings.__fields__.keys()
        settings_in_db = await get_login_setting(self.db)

        for item in settings_in_db:
            if item.key in fields:
                setattr(settings, item.key, json.loads(item.value))
        return settings

    @property
    def login_settings(self):
        async def dependency() -> LoginSettings:
            return await self.get_login_settings()

        return dependency
