from __future__ import annotations

import edgedb
from fastapi import FastAPI  # type: ignore

from .app import FreeAuthApp


class FreeAuthTestApp(FreeAuthApp):
    def __init__(self, app: FastAPI = None):
        self._edgedb_tx: edgedb.AsyncIOClient | None = None

        super().__init__(app)

    async def setup_edgedb(self) -> None:
        self._edgedb_client = client = edgedb.create_async_client(
            dsn=self.settings.edgedb_dsn or self.settings.edgedb_instance,
            database=self.settings.edgedb_database,
        )
        await client.ensure_connected()
        async for tx in client.with_retry_options(
            edgedb.RetryOptions(0)
        ).transaction():
            await tx.__aenter__()
            self.db = tx
            break

    async def shutdown_edgedb(self) -> None:
        await self.db.__aexit__(Exception, Exception(), None)
        await self._edgedb_client.aclose()

    @property
    def db(self) -> edgedb.AsyncIOClient:
        if not self._edgedb_tx:
            raise RuntimeError("Can't find edgedb client")
        return self._edgedb_tx

    @db.setter
    def db(self, tx: edgedb.AsyncIOClient):
        self._edgedb_tx = tx
