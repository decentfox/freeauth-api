from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_app(app: FastAPI, test_client: AsyncClient):
    @app.get("/")
    async def index() -> dict[str, str]:
        return {"Hello": "World"}

    resp = await test_client.get("/")

    assert resp.status_code == 200
    assert resp.json() == {"Hello": "World"}
