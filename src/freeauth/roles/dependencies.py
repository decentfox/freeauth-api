from __future__ import annotations

import uuid

from fastapi import Path


def parse_role_id_or_code(
    id_or_code: str = Path(title="角色 ID 或角色代码"),
) -> str | uuid.UUID:
    try:
        return uuid.UUID(id_or_code)
    except ValueError:
        return id_or_code
