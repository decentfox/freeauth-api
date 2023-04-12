from __future__ import annotations

import asyncio
import pathlib
from collections.abc import AsyncGenerator

import edgedb
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from freeauth.app import get_app

TEST_DBNAME = "testdb"


@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def db():
    default_cli = edgedb.create_async_client()
    databases = await default_cli.query("select {sys::Database.name}")
    if TEST_DBNAME in databases:
        await default_cli.execute(f"DROP DATABASE {TEST_DBNAME}")
    await default_cli.execute(f"CREATE DATABASE {TEST_DBNAME}")
    await default_cli.aclose()

    client = edgedb.create_async_client(database=TEST_DBNAME)

    for file_or_dir in sorted(pathlib.Path("dbschema/migrations").iterdir()):
        with file_or_dir.open() as f:
            query = f.read()
        await client.execute(query)
    yield client


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
    mocker.patch("freeauth.app.setup_edgedb", tx_setup_edgedb)
    mocker.patch("freeauth.app.shutdown_edgedb", tx_shutdown_edgedb)
    return get_app()


@pytest.fixture
def test_client(app):
    with TestClient(app) as client:
        yield client


async def tx_setup_edgedb(app):
    client = app.state.edgedb_client = edgedb.create_async_client(
        database=TEST_DBNAME
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
