import functools

import edgedb
from fastapi import FastAPI

from .admin import users


async def setup_edgedb(app):
    client = app.state.edgedb = edgedb.create_async_client()
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


def get_app():
    app = FastAPI(
        title="FreeAuth", description="Async REST API in Python for FreeAuth."
    )

    app.on_event("startup")(functools.partial(setup_edgedb, app))
    app.on_event("shutdown")(functools.partial(shutdown_edgedb, app))

    @app.get("/ping", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {"status": "Ok"}

    app.include_router(users.router)

    return app
