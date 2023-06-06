from __future__ import annotations

import uuid
from http import HTTPStatus

from fastapi import Depends, HTTPException, Query

from freeauth.db.admin.admin_qry_async_edgeql import (
    DeleteApplicationResult,
    QueryApplicationOptionsResult,
    UpdateApplicationStatusResult,
    create_application,
    delete_application,
    query_application_options,
    update_application_secret,
    update_application_status,
)
from freeauth.security.utils import gen_random_string, get_password_hash

from ..app import auth_app, router
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
    dependencies=[Depends(auth_app.perm_accepted("manage:apps"))],
)
async def post_application(
    body: BaseApplicationBody,
) -> dict[str, str]:
    secret: str = gen_random_string(32, secret=True)
    await create_application(
        auth_app.db,
        name=body.name,
        description=body.description,
        hashed_secret=get_password_hash(secret),
    )
    return {"secret": secret}


@router.put(
    "/applications/{app_id}/secret",
    tags=["应用管理"],
    summary="重新生成应用秘钥",
    description="重新生成指定应用的秘钥",
    dependencies=[Depends(auth_app.perm_accepted("manage:apps"))],
)
async def gen_application_secret(
    app_id: uuid.UUID,
) -> dict[str, str]:
    secret: str = gen_random_string(32, secret=True)
    application = await update_application_secret(
        auth_app.db,
        id=app_id,
        hashed_secret=get_password_hash(secret),
    )
    if not application:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="应用不存在"
        )
    return {"secret": secret}


@router.put(
    "/applications/status",
    tags=["应用管理"],
    summary="变更应用状态",
    description="批量变更应用状态",
    dependencies=[Depends(auth_app.perm_accepted("manage:apps"))],
)
async def toggle_applications_status(
    body: ApplicationStatusBody,
) -> list[UpdateApplicationStatusResult]:
    return await update_application_status(
        auth_app.db, ids=body.ids, is_deleted=body.is_deleted
    )


@router.delete(
    "/applications",
    tags=["应用管理"],
    summary="删除应用",
    description="批量删除应用",
    dependencies=[Depends(auth_app.perm_accepted("manage:apps"))],
)
async def delete_applications(
    body: ApplicationDeleteBody,
) -> list[DeleteApplicationResult]:
    return await delete_application(auth_app.db, ids=body.ids)


@router.post(
    "/applications/query",
    tags=["应用管理"],
    summary="获取应用列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
    dependencies=[Depends(auth_app.perm_accepted("manage:apps"))],
)
async def get_applications(
    body: QueryBody,
) -> PaginatedData:
    filtering_expr = body.get_filtering_expr(FILTER_TYPE_MAPPING)
    result = await auth_app.db.query_single_json(
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


@router.get(
    "/applications/options",
    tags=["应用管理"],
    summary="获取应用选项列表",
    description="获取应用选项列表，支持关键字搜索",
    dependencies=[
        Depends(auth_app.perm_accepted("manage:perms", "manage:roles"))
    ],
)
async def list_application_options(
    q: str
    | None = Query(
        None,
        title="搜索关键字",
        description="支持搜索应用名、应用描述",
    )
) -> list[QueryApplicationOptionsResult]:
    return await query_application_options(
        auth_app.db, q=f"%{q}%" if q else None
    )
