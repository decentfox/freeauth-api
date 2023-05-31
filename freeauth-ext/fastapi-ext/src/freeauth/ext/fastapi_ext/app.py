from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Callable

import edgedb
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from jose import ExpiredSignatureError, JWTError, jwt

from freeauth.conf.login_settings import LoginSettings
from freeauth.conf.settings import get_settings
from freeauth.db.admin.admin_qry_async_edgeql import add_missing_permissions
from freeauth.db.auth.auth_qry_async_edgeql import (
    GetCurrentUserResult,
    GetUserByAccessTokenResult,
    get_current_user,
    get_login_setting,
    get_user_by_access_token,
    has_any_permission,
)
from freeauth.security import FreeAuthSecurity

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
        self.security = FreeAuthSecurity()

        if app is not None:
            self.init_app(app)

    def init_app(self, app: FastAPI) -> None:
        self.app = app

        self.app.add_event_handler("startup", self.setup_edgedb)
        self.app.add_event_handler("startup", self.migrate_perms)
        self.app.add_event_handler("shutdown", self.shutdown_edgedb)

    async def setup_edgedb(self) -> None:
        client = edgedb.create_async_client(
            dsn=self.settings.edgedb_dsn or self.settings.edgedb_instance,
            database=self.settings.edgedb_database,
        )
        await client.ensure_connected()
        self.db = client.with_globals(
            current_app_id=self.settings.freeauth_app_id
        )

    async def shutdown_edgedb(self) -> None:
        await self.db.aclose()

    async def migrate_perms(self) -> None:
        perm_codes = [perm.code for perm in self.security.permissions]
        if perm_codes:
            await add_missing_permissions(self.db, perm_codes=perm_codes)

    @property
    def db(self) -> edgedb.AsyncIOClient:
        if not self._edgedb_client:
            raise RuntimeError("Can't find edgedb client")
        return self._edgedb_client

    @db.setter
    def db(self, client):
        self._edgedb_client = client

    def with_globals(self, *args, **globals_):
        return self.db.with_globals(*args, **globals_)

    async def create_access_token(
        self, response: Response, user_id: uuid.UUID
    ) -> str:
        now = datetime.utcnow()
        login_settings = await self.get_login_settings()
        jwt_token_ttl = login_settings.jwt_token_ttl
        payload = {
            "sub": str(user_id),
            "exp": now + timedelta(
                minutes=jwt_token_ttl or self.settings.jwt_token_ttl
            ),
        }
        token = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        response.set_cookie(
            key=self.settings.jwt_cookie_key,
            value=token,
            httponly=True,
            secure=self.settings.jwt_cookie_secure,
            max_age=jwt_token_ttl * 60 if jwt_token_ttl else None,
            samesite="strict",
        )
        return token

    async def get_access_token(
        self, request: Request
    ) -> GetUserByAccessTokenResult | None:
        access_token: str | None = request.cookies.get(
            self.settings.jwt_cookie_key
        )
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
            token: GetUserByAccessTokenResult | None = (
                await get_user_by_access_token(
                    self.db, access_token=access_token
                )
            )
            if not token:
                logger.info("token not found")
                return None

            user_id = payload.get("sub")
            if user_id != str(token.user.id):
                logger.info("user mismatches in token")
                return None
        return token

    @property
    def user_scoped_db(self) -> Callable:
        async def dependency(
            access_token: GetUserByAccessTokenResult
            | None = Depends(self.get_access_token),
        ) -> edgedb.AsyncIOClient | None:
            if not access_token:
                return None
            return self.with_globals(current_user_id=access_token.user.id)

        return dependency

    @property
    def current_user(self) -> Callable:
        async def dependency(
            db: edgedb.AsyncIOClient | None = Depends(self.user_scoped_db),
        ) -> GetCurrentUserResult | None:
            if db:
                return await get_current_user(db)
            return None

        return dependency

    @property
    def current_user_or_401(self) -> Callable:
        async def dependency(
            current_user: GetCurrentUserResult
            | None = Depends(self.current_user),
        ) -> GetCurrentUserResult:
            if not current_user or current_user.is_deleted:
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED, detail="身份验证失败"
                )

            return current_user

        return dependency

    def perm_accepted(self, *perm_codes: str) -> Callable:
        async def dependency(
            db: edgedb.AsyncIOClient = Depends(self.user_scoped_db),
            user: GetCurrentUserResult = Depends(self.current_user_or_401),
        ) -> GetCurrentUserResult:
            if not await has_any_permission(db, perm_codes=list(perm_codes)):
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN, detail="您无权进行该操作"
                )
            return user

        self.security.add_perm(*perm_codes)
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
