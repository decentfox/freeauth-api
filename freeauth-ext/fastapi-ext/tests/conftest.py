import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from freeauth.ext.fastapi_ext import FreeAuthTestApp


@pytest.fixture
def app():
    return FastAPI()


@pytest.fixture
def auth_app(app):
    return FreeAuthTestApp(app)


@pytest.fixture
def test_client(app):
    with TestClient(app) as client:
        yield client
