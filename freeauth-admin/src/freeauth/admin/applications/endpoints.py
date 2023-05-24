from __future__ import annotations

from http import HTTPStatus

import edgedb
from fastapi import Depends

from freeauth.db.admin.admin_qry_async_edgeql import (
    CreateApplicationResult,
    DeleteApplicationResult,
    UpdateApplicationStatusResult,
    create_application,
    delete_application,
    update_application_status,
)

from .. import get_edgedb_client
from ..app import router
from ..dataclasses import PaginatedData, QueryBody
from .dataclasses import (
    ApplicationDeleteBody,
    ApplicationStatusBody,
    BaseApplicationBody,
)

FILTER_TYPE_MAPPING = {"created_at": "datetime", "is_deleted": "bool"}


@router.post(
    "/applications",
    status_code=HTTPStatus.CREATED,
    tags=["应用管理"],
    summary="创建应用",
    description="创建新应用",
)
async def post_application(
    body: BaseApplicationBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> CreateApplicationResult:
    application = await create_application(
        client,
        name=body.name,
        description=body.description,
    )
    return application


@router.put(
    "/applications/status",
    tags=["应用管理"],
    summary="变更应用状态",
    description="批量变更应用状态",
)
async def toggle_applications_status(
    body: ApplicationStatusBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[UpdateApplicationStatusResult]:
    return await update_application_status(
        client, ids=body.ids, is_deleted=body.is_deleted
    )


@router.delete(
    "/applications",
    tags=["应用管理"],
    summary="删除应用",
    description="批量删除应用",
)
async def delete_applications(
    body: ApplicationDeleteBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> list[DeleteApplicationResult]:
    return await delete_application(client, ids=body.ids)


@router.post(
    "/applications/query",
    tags=["应用管理"],
    summary="获取应用列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
)
async def get_applications(
    body: QueryBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    filtering_expr = body.get_filtering_expr(FILTER_TYPE_MAPPING)
    result = await client.query_single_json(
        f"""\
            with
                page := <optional int64>$page ?? 1,
                per_page := <optional int64>$per_page ?? 20,
                q := <optional str>$q,
                applications := (
                    select Application
                    filter (
                        true IF not EXISTS q ELSE
                        .name ILIKE q OR
                        .description ?? '' ILIKE q
                    ) AND {filtering_expr}
                ),
                total := count(applications)

            select (
                total := total,
                per_page := per_page,
                page := page,
                last := math::ceil(total / per_page),
                rows := array_agg((
                    select applications {{
                        id,
                        name,
                        description,
                        secret_key,
                        is_protected,
                        is_deleted,
                        created_at
                    }}
                    ORDER BY {body.ordering_expr}
                    OFFSET (page - 1) * per_page
                    LIMIT per_page
                ))
            );\
            """,
        q=f"%{body.q}%" if body.q else None,
        page=body.page,
        per_page=body.per_page,
    )
    return PaginatedData.parse_raw(result)
