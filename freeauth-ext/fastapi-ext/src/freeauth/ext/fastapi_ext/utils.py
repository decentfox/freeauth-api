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

from fastapi import Request

from . import user_agent_parser


def get_client_info(request: Request) -> dict:
    raw_ua: str | None = request.headers.get("User-Agent")
    user_agent = dict(
        raw_ua=raw_ua,
    )
    if raw_ua:
        ua = user_agent_parser.Parse(raw_ua)  # type: ignore[attr-defined]
        user_agent.update(
            os=ua["os"]["family"],
            device=ua["device"]["family"],
            browser=ua["user_agent"]["family"],
        )
    return {
        "client_ip": request.headers.get(
            "X-Forwarded-For", request.client.host if request.client else None
        ),
        "user_agent": user_agent,
    }
