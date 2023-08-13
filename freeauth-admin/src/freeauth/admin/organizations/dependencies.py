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

import uuid
from http import HTTPStatus

from fastapi import HTTPException, Path, Query


def parse_org_type_id_or_code(
    id_or_code: str = Path(title="组织类型 ID 或 Code"),
) -> str | uuid.UUID:
    try:
        return uuid.UUID(id_or_code)
    except ValueError:
        return id_or_code


def parse_enterprise_id_or_code(
    id_or_code: str = Path(title="企业机构 ID 或 Code"),
    org_type_id_or_code: str = Query(
        None,
        title="组织类型 ID 或 Code",
        description=(
            "当通过企业机构 Code 调用接口时，需同时指定所属的组织类型的 ID 或"
            " Code"
        ),
    ),
) -> tuple[str | uuid.UUID, str | uuid.UUID | None]:
    try:
        return uuid.UUID(id_or_code), None
    except ValueError:
        pass
    if not org_type_id_or_code:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="缺少组织类型 ID 或 Code",
        )
    try:
        return id_or_code, uuid.UUID(org_type_id_or_code)
    except ValueError:
        return id_or_code, org_type_id_or_code


def parse_department_id_or_code(
    id_or_code: str = Path(title="部门 ID 或 Code"),
    enterprise_id: uuid.UUID = Query(
        None,
        title="企业机构 ID",
        description="当通过部门 Code 调用接口时，需同时指定所属企业机构的 ID",
    ),
) -> tuple[str | uuid.UUID, uuid.UUID | None]:
    try:
        return uuid.UUID(id_or_code), None
    except ValueError:
        pass
    if not enterprise_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="缺少企业机构 ID",
        )
    return id_or_code, enterprise_id
