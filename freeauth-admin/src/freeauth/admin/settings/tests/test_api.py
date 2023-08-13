# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan
# PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from __future__ import annotations

import re
from http import HTTPStatus
from typing import Any

from fastapi.testclient import TestClient

from freeauth.conf.login_settings import LoginSettings


def test_get_default_login_settings(bo_client: TestClient):
    settings = LoginSettings()
    resp = bo_client.get("/v1/login_settings")
    ret = resp.json()
    assert resp.status_code == HTTPStatus.OK, ret
    for key, value in ret.items():
        snake_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
        assert getattr(settings, snake_key) == value


def test_update_login_settings(bo_client: TestClient):
    resp = bo_client.put("/v1/login_settings", json={})
    assert resp.status_code == HTTPStatus.OK, resp.json()

    data: dict[str, Any] = dict(invalidKey="new value")
    resp = bo_client.put("/v1/login_settings", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert "系统不支持登录配置项 invalidKey" in error["detail"]["message"]

    data = dict(
        guardTitle="new value",
        guardPrimaryColor="#ffffff",
    )
    resp = bo_client.put("/v1/login_settings", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["guardTitle"] == "new value"
    assert rv["guardPrimaryColor"] == "#ffffff"

    data = dict(jwtTokenTtl=1440)
    resp = bo_client.put("/v1/login_settings", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv["jwtTokenTtl"] == 1440

    resp = bo_client.get("/v1/login_settings")
    ret = resp.json()
    assert resp.status_code == HTTPStatus.OK, ret
    assert ret["guardTitle"] == "new value"
    assert ret["guardPrimaryColor"] == "#ffffff"
    assert ret["jwtTokenTtl"] == 1440
