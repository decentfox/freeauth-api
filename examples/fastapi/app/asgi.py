from __future__ import annotations

from fastapi import APIRouter, FastAPI
from freeauth.ext.fastapi_ext import FreeAuthApp

router = APIRouter(prefix="/v1")
auth_app = FreeAuthApp()


def get_app():
    app = FastAPI()
    auth_app.init_app(app)

    @app.get("/ping", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {"status": "Ok"}

    app.include_router(router)

    return app


fast_api = get_app()
