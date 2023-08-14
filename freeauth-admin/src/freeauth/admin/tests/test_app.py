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

from http import HTTPStatus

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_app(app: FastAPI, test_client: TestClient):
    @app.get("/")
    async def index() -> dict[str, str]:
        return {"Hello": "World"}

    resp = test_client.get("/")

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"Hello": "World"}

    resp = test_client.get("/ping")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"status": "Ok"}
