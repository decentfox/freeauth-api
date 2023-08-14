# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from __future__ import annotations

import functools

import edgedb
from fastapi import APIRouter, FastAPI, Request
from freeauth.conf.settings import get_settings
from freeauth.ext.fastapi_ext import FreeAuthApp

router = APIRouter(prefix="/v1")
auth_app = FreeAuthApp()


async def setup_edgedb(app):
    settings = get_settings()
    client = app.state.edgedb = edgedb.create_async_client(
        dsn=settings.edgedb_dsn or settings.edgedb_instance,
        database=settings.edgedb_database,
    )
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


def get_edgedb_client(request: Request) -> edgedb.AsyncIOClient:
    return request.app.state.edgedb


def get_app():
    app = FastAPI()

    app.add_event_handler("startup", functools.partial(setup_edgedb, app))
    app.add_event_handler("shutdown", functools.partial(shutdown_edgedb, app))

    auth_app.init_app(app)

    @app.get("/ping", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {"status": "Ok"}

    from . import movie  # noqa
    from . import security  # noqa

    app.include_router(router)

    return app


fast_api = get_app()
