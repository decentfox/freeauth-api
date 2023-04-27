from __future__ import annotations

from http import HTTPStatus

from fastapi.testclient import TestClient

from .. import get_login_settings


def test_get_default_login_settings(test_client: TestClient):
    settings = get_login_settings()
    resp = test_client.get("/v1/login_settings")
    ret = resp.json()
    assert resp.status_code == HTTPStatus.OK, ret
    assert not settings._empty
    for key, value in ret.items():
        assert getattr(settings, key) == value


def test_update_login_settings(test_client: TestClient):
    resp = test_client.put("/v1/login_settings/invalid-key", json={})
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert error["detail"]["errors"]["value"] == "该字段为必填项"

    data = dict(value="new value")
    resp = test_client.put("/v1/login_settings/invalid-key", json=data)
    error = resp.json()
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, error
    assert "系统不支持该登录配置项" in error["detail"]["message"]

    resp = test_client.put("/v1/login_settings/guard_title", json=data)
    rv = resp.json()
    assert resp.status_code == HTTPStatus.OK, rv
    assert rv == {"guard_title": "new value"}

    resp = test_client.get("/v1/login_settings")
    ret = resp.json()
    assert resp.status_code == HTTPStatus.OK, ret
    assert ret["guard_title"] == "new value"

    settings = get_login_settings()
    data["value"] = settings.guard_title
    resp = test_client.put("/v1/login_settings/guard_title", json=data)
    assert resp.status_code == HTTPStatus.OK, resp.json()
