import pytest
from fastapi.testclient import TestClient

from freeauth.app import get_app


@pytest.fixture
def app():
    return get_app()


@pytest.fixture
def client(app):
    return TestClient(app)


async def test_app(app, client):
    @app.get("/")
    async def index():
        return {"Hello": "World"}

    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.json() == {"Hello": "World"}
