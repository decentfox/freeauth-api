from fastapi import Depends
from fastapi.testclient import TestClient

from freeauth.ext.fastapi_ext.utils import get_client_info


def test_get_client_info(app):
    @app.get("/client_info")
    async def get_user_client_info(
        client_info: dict = Depends(get_client_info),
    ) -> dict:
        return client_info

    with TestClient(
        app,
        headers={
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/112.0.0.0 Safari/537.36"
            ),
            "x-forwarded-for": "162.158.233.39",
        },
    ) as client:
        resp = client.get("/client_info")

    rv = resp.json()
    assert rv["client_ip"] == "162.158.233.39"
    user_agent = rv["user_agent"]
    assert user_agent["os"] == "Mac OS X"
    assert user_agent["device"] == "Mac"
    assert user_agent["browser"] == "Chrome"
