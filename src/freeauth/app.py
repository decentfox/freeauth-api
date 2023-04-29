from __future__ import annotations

import functools
from typing import Dict, Union, cast

import edgedb
from fastapi import APIRouter, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from .config import get_config
from .log import configure_logging

router = APIRouter(prefix="/v1")


async def setup_edgedb(app):
    client = app.state.edgedb = edgedb.create_async_client()
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


async def http_exception_accept_handler(
    request: Request,
    exc: Union[RequestValidationError, StarletteHTTPException],
) -> Response:
    message = "请求失败"
    if request.scope.get("route"):
        message = f"{request.scope['route'].summary or '请求'}失败"
    if isinstance(exc, RequestValidationError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
        raw_errors = exc.raw_errors
        error_wrapper: ErrorWrapper = cast(ErrorWrapper, raw_errors[0])
        validation_error: ValidationError = cast(
            ValidationError, error_wrapper.exc
        )
        try:
            overwritten_errors = validation_error.errors()
            detail = jsonable_encoder(overwritten_errors)
            errors: Dict[str, str] = {}
            for err in detail:
                errors[".".join(str(i) for i in err["loc"])] = err["msg"]
            detail = dict(
                message=message,
                errors=errors,
            )
        except AttributeError:
            detail = dict(message=f"{message}：{validation_error}")
    else:
        status_code = exc.status_code
        if isinstance(exc.detail, str):
            detail = dict(message=f"{message}：{exc.detail}")
        else:
            detail = dict(
                message=message,
                errors=exc.detail,
            )
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )


def get_app():
    config = get_config()
    app = FastAPI(
        debug=config.debug,
        title="FreeAuth",
        description="Async REST API in Python for FreeAuth.",
        exception_handlers={
            StarletteHTTPException: http_exception_accept_handler,
            RequestValidationError: http_exception_accept_handler,
        },
    )
    configure_logging(app)

    app.on_event("startup")(functools.partial(setup_edgedb, app))
    app.on_event("shutdown")(functools.partial(shutdown_edgedb, app))

    @app.get("/ping", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {"status": "Ok"}

    from .audit_logs import endpoints  # noqa
    from .auth import endpoints  # noqa
    from .organizations import endpoints  # noqa
    from .settings import endpoints  # noqa
    from .users import endpoints  # noqa

    app.include_router(router)

    return app
