import os

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from freeauth.ext.fastapi_ext import FreeAuthTestApp


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    orig_env = os.environ.copy()
    os.environ["EDGEDB_DATABASE"] = "testdb"
    os.environ["TESTING"] = "true"
    os.environ["JWT_COOKIE_SECURE"] = "false"

    yield

    os.environ = orig_env


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


@pytest.fixture(scope="session", autouse=True)
def faker_locale():
    return ["zh_CN"]
