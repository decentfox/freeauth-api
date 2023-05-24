from __future__ import annotations

import asyncio
import os
import pathlib
from collections.abc import AsyncGenerator

import edgedb
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from freeauth import db as freeauth_db
from freeauth.conf.settings import get_settings
from freeauth.db.admin.admin_qry_async_edgeql import CreateUserResult

from . import app as freeauth_app


@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    orig_env = os.environ.copy()
    os.environ["EDGEDB_DATABASE"] = "testdb"
    os.environ["TESTING"] = "true"
    os.environ["JWT_COOKIE_SECURE"] = "false"
    os.environ["DEMO_ACCOUNTS"] = '["user@example.com", "13800000000"]'

    yield

    os.environ = orig_env


@pytest.fixture(scope="session", autouse=True)
async def db(setup_and_teardown, request):
    settings = get_settings()
    reset_db = request.config.getoption("--reset-db")
    default_cli = edgedb.create_async_client(database="edgedb")
    databases = await default_cli.query("select {sys::Database.name}")
    exists = settings.edgedb_database in databases
    if reset_db and exists:
        await default_cli.execute(f"drop database {settings.edgedb_database}")
    if reset_db or not exists:
        await default_cli.execute(
            f"create database {settings.edgedb_database}"
        )
    await default_cli.aclose()

    client = edgedb.create_async_client(database=settings.edgedb_database)

    if reset_db or not exists:
        schema_path = pathlib.Path(freeauth_db.__file__).parent.joinpath(
            "dbschema", "migrations"
        )
        for file_or_dir in sorted(schema_path.iterdir()):
            with file_or_dir.open() as f:
                query = f.read()
            await client.execute(query)
    yield client

    await client.aclose()


class Rollback(Exception):
    pass


@pytest.fixture
async def edgedb_client(db) -> AsyncGenerator[edgedb.AsyncIOClient, None]:
    try:
        async for tx in db.transaction():
            async with tx:
                yield tx
                raise Rollback
    except Rollback:
        pass


@pytest.fixture
def app(mocker) -> FastAPI:
    mocker.patch.object(freeauth_app, "setup_edgedb", tx_setup_edgedb)
    mocker.patch.object(freeauth_app, "shutdown_edgedb", tx_setup_edgedb)
    return freeauth_app.get_app()


@pytest.fixture
def test_client(app):
    with TestClient(
        app,
        headers={
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/112.0.0.0 Safari/537.36"
            ),
            "x-forwarded-for": "162.158.233.39",
        },
    ) as client:
        yield client


async def tx_setup_edgedb(app):
    settings = get_settings()
    client = app.state.edgedb_client = edgedb.create_async_client(
        database=settings.edgedb_database
    )
    await client.ensure_connected()
    async for tx in client.with_retry_options(
        edgedb.RetryOptions(0)
    ).transaction():
        await tx.__aenter__()
        app.state.edgedb = tx
        break


async def tx_shutdown_edgedb(app):
    client, app.state.edgedb_client = app.state.edgedb_client, None
    tx, app.state.edgedb = app.state.edgedb, None
    await tx.__aexit__(Exception, Exception(), None)
    await client.aclose()


@pytest.fixture(scope="session", autouse=True)
def faker_locale():
    return ["zh_CN"]


@pytest.fixture
def bo_user(test_client, faker) -> CreateUserResult:
    username = faker.user_name()
    resp = test_client.post(
        "/v1/users",
        json=dict(
            name=faker.name(),
            username=username,
            mobile=faker.phone_number(),
            email=faker.email(),
            password=username,
        ),
    )
    user = resp.json()
    return CreateUserResult(**user)


@pytest.fixture
def bo_user_client(test_client, bo_user) -> TestClient:
    test_client.post(
        "/v1/sign_in",
        json={
            "account": bo_user.username,
            "password": bo_user.username,
        },
    )
    return test_client
