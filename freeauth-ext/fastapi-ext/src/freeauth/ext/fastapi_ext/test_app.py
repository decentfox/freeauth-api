from __future__ import annotations

import edgedb
from fastapi import FastAPI

from .app import FreeAuthApp

__all__ = ["FreeAuthTestApp"]


class FreeAuthTestApp(FreeAuthApp):
    def __init__(self, app: FastAPI | None = None):
        self._edgedb_tx: edgedb.AsyncIOClient | None = None

        super().__init__(app)

    async def setup_edgedb(self) -> None:
        client = edgedb.create_async_client(
            dsn=self.settings.edgedb_dsn or self.settings.edgedb_instance,
            database=self.settings.edgedb_database,
        )
        await client.ensure_connected()
        self._edgedb_client = client = client.with_globals(
            current_app_id=self.settings.freeauth_app_id
        )
        async for tx in client.with_retry_options(
            edgedb.RetryOptions(0)
        ).transaction():
            await tx.__aenter__()
            self.db = tx
            break

    async def shutdown_edgedb(self) -> None:
        await self.db.__aexit__(Exception, Exception(), None)
        if self._edgedb_client:
            await self._edgedb_client.aclose()

    @property
    def db(self) -> edgedb.AsyncIOClient:
        if not self._edgedb_tx:
            raise RuntimeError("Can't find edgedb client")
        return self._edgedb_tx

    @db.setter
    def db(self, tx: edgedb.AsyncIOClient):
        self._edgedb_tx = tx

    def with_globals(self, *args, **globals_):
        state = self.db._get_state()
        state_globals = state._globals
        if args:
            for k, v in args[0].items():
                state_globals[state.resolve(k)] = v
        for k, v in globals_.items():
            state_globals[state.resolve(k)] = v
        return self.db
