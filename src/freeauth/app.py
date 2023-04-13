import functools
from typing import cast

import edgedb
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from .admin import users


async def setup_edgedb(app):
    client = app.state.edgedb = edgedb.create_async_client()
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


async def http_exception_accept_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    raw_errors = exc.raw_errors
    error_wrapper: ErrorWrapper = cast(ErrorWrapper, raw_errors[0])
    validation_error: ValidationError = cast(
        ValidationError, error_wrapper.exc
    )
    overwritten_errors = validation_error.errors()
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(overwritten_errors)},
    )


def get_app():
    app = FastAPI(
        title="FreeAuth",
        description="Async REST API in Python for FreeAuth.",
        exception_handlers={
            RequestValidationError: http_exception_accept_handler,
        },
    )

    app.on_event("startup")(functools.partial(setup_edgedb, app))
    app.on_event("shutdown")(functools.partial(shutdown_edgedb, app))

    @app.get("/ping", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {"status": "Ok"}

    app.include_router(users.router)

    return app
