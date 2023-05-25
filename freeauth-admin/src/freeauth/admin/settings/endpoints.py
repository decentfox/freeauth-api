from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any

from fastapi import Body, HTTPException

from ..app import auth_app, router
from . import get_login_settings


async def load_login_configs():
    settings = await get_login_settings().get_all(auth_app.db)
    ret = {}
    for key, value in settings.items():
        camel_key = re.sub(r"_(\w)", lambda m: m.group(1).upper(), key)
        ret[camel_key] = value
    return ret


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
)
async def put_login_configs(
    body: dict[str, Any] = Body(
        ...,
        title="登录配置项键值",
        description="登录配置项键值，支持任意 JSON 可解析的格式的配置值",
    ),
) -> dict[str, Any]:
    settings = get_login_settings()
    keys = settings.get_keys()
    configs = {}
    for key in body.keys():
        snake_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()

        if snake_key not in keys:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=f"系统不支持登录配置项 {key}",
            )

        configs[snake_key] = body[key]
    await settings.patch(configs, auth_app.db)
    return await load_login_configs()