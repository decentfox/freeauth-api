from __future__ import annotations

import uuid
from http import HTTPStatus

import edgedb
from fastapi import Depends, HTTPException, Path

from .. import get_edgedb_client
from ..query_api import validate_role_organization_ids
from .dataclasses import RolePostBody


def parse_role_id_or_code(
    id_or_code: str = Path(title="角色 ID 或角色代码"),
) -> str | uuid.UUID:
    try:
        return uuid.UUID(id_or_code)
    except ValueError:
        return id_or_code


async def validate_organization_ids(
    body: RolePostBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
):
    if not body.organization_ids:
        return

    invalid = await validate_role_organization_ids(
        client, organization_ids=body.organization_ids
    )

    if invalid:
        names = "、".join(f'"{o}"' for o in invalid)
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={
                "organization_ids": (
                    f"{names}已包含在其他所属对象中，无需重复设置"
                )
            },
        )
