from __future__ import annotations

import json
from http import HTTPStatus

import pytest
from fastapi import Depends, Response

from freeauth.conf.login_settings import LoginSettings
from freeauth.db.auth.auth_qry_async_edgeql import (
    GetUserByAccessTokenResult,
    sign_in,
    sign_up,
)
from freeauth.ext.fastapi_ext.utils import get_client_info


def test_auth_app_db(app, auth_app, test_client):
    @app.get("/numbers")
    async def get_numbers() -> list[int]:
        return await auth_app.db.query("select {1, 2, 3}")

    @app.get("/strings")
    async def get_strings() -> list[str]:
        return await auth_app.db.query("select {1, 2, 3}")

    resp = test_client.get("/numbers")
    assert resp.json() == [1, 2, 3]

    resp = test_client.get("/strings")
    assert resp.json() == ["1", "2", "3"]


def test_get_login_settings(app, auth_app, test_client):
    @app.get("/login_settings", response_model=LoginSettings)
    async def login_settings(
        settings: LoginSettings = Depends(auth_app.login_settings),
    ) -> LoginSettings:
        return settings

    resp = test_client.get("/login_settings")
    rv = resp.json()

    assert rv.keys() == LoginSettings.__fields__.keys()


@pytest.fixture
def example_app(app, auth_app, test_client, faker):
    @app.post("/sign_up")
    async def user_sign_up(
        response: Response,
        client_info: dict = Depends(get_client_info),
    ):
        ci = json.dumps(client_info)
        user = await sign_up(
            auth_app.db,
            name=faker.name(),
            username=faker.user_name(),
            mobile=faker.phone_number(),
            email=faker.email(),
            hashed_password="",
            client_info=ci,
        )
        token = await auth_app.create_access_token(response, user.id)
        return await sign_in(
            auth_app.db,
            id=user.id,
            access_token=token,
            client_info=ci,
        )

    @app.get("/me")
    async def get_user_me(
        current_user: GetUserByAccessTokenResult = Depends(
            auth_app.current_user_or_401
        ),
    ):
        return current_user


def test_get_current_user(example_app, test_client):
    resp = test_client.get("/me")
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNAUTHORIZED, error
    assert error["detail"] == "身份验证失败"

    resp = test_client.post("/sign_up")
    assert resp.status_code == HTTPStatus.OK, resp.json()

    resp = test_client.get("/me")
    assert resp.status_code == HTTPStatus.OK, resp.json()
