from __future__ import annotations

import uuid

from fastapi import Path


def parse_id_or_code(id_or_code: str = Path()) -> str | uuid.UUID:
    try:
        return uuid.UUID(id_or_code)
    except ValueError:
        return id_or_code
