from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_app(app: FastAPI, test_client: TestClient):
    @app.get("/")
    async def index() -> dict[str, str]:
        return {"Hello": "World"}

    resp = test_client.get("/")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"Hello": "World"}

    resp = test_client.get("/ping")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"status": "Ok"}
