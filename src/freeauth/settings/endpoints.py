from __future__ import annotations

from http import HTTPStatus
from typing import Any

import edgedb
from fastapi import Depends, HTTPException

from .. import get_edgedb_client
from ..app import router
from . import LoginSettings, get_login_settings
from .forms import LoginSettingBody


def get_setting_keys():
    return [
        x
        for x in vars(LoginSettings).keys()
        if not callable(getattr(LoginSettings, x)) and not x.startswith("_")
    ]


@router.get(
    "/login_settings",
    tags=["登录配置"],
    summary="获取登录配置项",
    description="获取系统中的登录配置项键值",
)
async def get_login_configs(
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    keys: list[str] = Depends(get_setting_keys),
) -> dict[str, Any]:
    settings = get_login_settings()
    ret = {}
    for key in keys:
        value = await settings.get(key, client)
        ret[key] = value
    return ret


@router.put(
    "/login_settings/{key}",
    tags=["登录配置"],
    summary="更新登录配置项",
    description="更新指定登录配置项",
)
async def put_config(
    key: str,
    body: LoginSettingBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
    keys: list[str] = Depends(get_setting_keys),
) -> dict[str, Any]:
    if key not in keys:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="系统不支持该登录配置项",
        )
    settings = get_login_settings()
    return await settings.set(key, body.value, client)
