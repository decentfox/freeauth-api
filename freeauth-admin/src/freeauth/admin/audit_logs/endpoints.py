from __future__ import annotations

from fastapi import Depends

from ..app import auth_app, router
from ..dataclasses import PaginatedData, QueryBody

FILTER_TYPE_MAPPING = {
    "event_type": "auth::AuditEventType",
    "created_at": "datetime",
    "is_succeed": "bool",
}


@router.post(
    "/audit_logs/query",
    tags=["审计日志"],
    summary="获取审计日志列表",
    description="分页获取，支持关键字搜索、排序及条件过滤",
    dependencies=[Depends(auth_app.perm_accepted("manage:audit_logs"))],
)
async def query_audit_logs(
    body: QueryBody,
) -> PaginatedData:
    filtering_expr = body.get_filtering_expr(FILTER_TYPE_MAPPING)
    result = await auth_app.db.query_single_json(
        f"""\
        WITH
            page := <optional int64>$page ?? 1,
            per_page := <optional int64>$per_page ?? 20,
            q := <optional str>$q,
            audit_logs := (
                SELECT auth::AuditLog
                FILTER (
                    true IF not EXISTS q ELSE
                    .raw_ua ?? '' ILIKE q OR
                    .client_ip ?? '' ILIKE q OR
                    .user.name ?? '' ILIKE q OR
                    .user.username ?? '' ILIKE q OR
                    .user.mobile ?? '' ILIKE q OR
                    .user.email ?? '' ILIKE q
                ) AND {filtering_expr}
            ),
            total := count(audit_logs)
        SELECT (
            total := total,
            per_page := per_page,
            page := page,
            last := math::ceil(total / per_page),
            rows := array_agg((
                SELECT audit_logs {{
                    id,
                    event_type,
                    user: {{
                        id,
                        name,
                        username,
                        email,
                        mobile,
                    }},
                    client_ip,
                    os,
                    device,
                    browser,
                    status_code,
                    is_succeed,
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
