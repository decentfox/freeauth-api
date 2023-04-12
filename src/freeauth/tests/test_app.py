from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_app(app: FastAPI, test_client: TestClient):
    @app.get("/")
    async def index() -> dict[str, str]:
        return {"Hello": "World"}

    resp = test_client.get("/")

    assert resp.status_code == 200
    assert resp.json() == {"Hello": "World"}
