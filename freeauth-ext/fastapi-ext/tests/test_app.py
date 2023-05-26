from __future__ import annotations

from fastapi import Depends

from freeauth.conf.login_settings import LoginSettings


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
