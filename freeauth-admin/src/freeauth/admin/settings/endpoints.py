from __future__ import annotations

import json
import re
from http import HTTPStatus
from typing import Any

from fastapi import Body, Depends, HTTPException

from freeauth.conf.login_settings import LoginSettings
from freeauth.db.auth.auth_qry_async_edgeql import upsert_login_setting

from ..app import auth_app, router


async def load_login_configs() -> dict[str, Any]:
    settings: LoginSettings = await auth_app.get_login_settings()
    return {
        re.sub(r"_(\w)", lambda m: m.group(1).upper(), k): v
        for k, v in settings.dict().items()
    }


@router.get(
    "/login_settings",
    tags=["登录配置"],
    summary="获取登录配置项",
    description="获取系统中的登录配置项键值",
)
async def get_login_configs() -> dict[str, Any]:
    return await load_login_configs()


@router.put(
    "/login_settings",
    tags=["登录配置"],
    summary="更新登录配置项",
    description="更新一个或多个登录配置项值",
    dependencies=[Depends(auth_app.perm_accepted("manage:login_settings"))],
)
async def put_login_configs(
    body: dict[str, Any] = Body(
        ...,
        title="登录配置项键值",
        description="登录配置项键值，支持任意 JSON 可解析的格式的配置值",
    ),
) -> dict[str, Any]:
    keys = LoginSettings.__fields__.keys()
    configs = {}
    for key in body.keys():
        snake_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()

        if snake_key not in keys:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"系统不支持登录配置项 {key}",
            )

        configs[snake_key] = body[key]

    await upsert_login_setting(auth_app.db, configs=json.dumps(configs))
    return await load_login_configs()
