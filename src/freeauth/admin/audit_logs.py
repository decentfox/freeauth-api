from __future__ import annotations

import edgedb
from fastapi import APIRouter, Depends

from .. import get_edgedb_client
from .common import PaginatedData, QueryBody

router = APIRouter(tags=["审计日志"])


@router.post(
    "/audit_logs/query",
    summary="获取审计日志列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
)
async def query_audit_logs(
    body: QueryBody,
    client: edgedb.AsyncIOClient = Depends(get_edgedb_client),
) -> PaginatedData:
    result = await client.query_single_json(
        f"""\
        WITH
            page := <optional int64>$page ?? 1,
            per_page := <optional int64>$per_page ?? 20,
            q := <optional str>$q,
            audit_logs := (SELECT auth::AuditLog),
            total := count(audit_logs)
        SELECT (
            total := total,
            per_page := per_page,
            page := page,
            last := math::ceil(total / per_page),
            rows := array_agg((
                SELECT audit_logs {{
                    event_type,
                    user: {{
                        username,
                        email,
                        mobile,
                    }},
                    client_ip,
                    os,
                    device,
                    browser,
                    status_code,
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
