from __future__ import annotations

import logging

import edgedb
from fastapi import Request

logger = logging.getLogger(__name__)


def get_edgedb_client(request: Request) -> edgedb.AsyncIOClient:
    return request.app.state.edgedb
