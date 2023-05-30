from __future__ import annotations

from fastapi import Request
from user_agents import parse as ua_parse  # type: ignore


def get_client_info(request: Request) -> dict:
    raw_ua: str | None = request.headers.get("User-Agent")
    user_agent = dict(
        raw_ua=raw_ua,
    )
    if raw_ua:
        ua = ua_parse(raw_ua)
        user_agent.update(
            os=ua.os.family,
            device=ua.device.family,
            browser=ua.browser.family,
        )
    return {
        "client_ip": request.headers.get(
            "X-Forwarded-For", request.client.host if request.client else None
        ),
        "user_agent": user_agent,
    }
