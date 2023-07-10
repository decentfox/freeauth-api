with
    module freeauth,
    page := <optional int64>$page ?? 1,
    per_page := <optional int64>$per_page ?? 20,
    q := <optional str>$q,
    application_id := <optional uuid>$application_id,
    tag_ids := <optional array<uuid>>$tag_ids,
    role := (
        select Role
        filter .id = <optional uuid>$role_id
    ),
    permissions := (
        select Permission
        filter (
            true if not exists q else
            .name ?? '' ilike q or
            .code ?? '' ilike q
        ) and (
            true if not exists application_id else
            .application.id = application_id
        ) and (
            all((
                for tag in array_unpack(tag_ids)
                union (tag in .tags.id)
            ))
        ) and (
            true if not exists role else
            role in .roles
        )
    ),
    total := count(permissions)
select {
    total := total,
    per_page := per_page,
    page := page,
    last := math::ceil(total / per_page),
    rows := array_agg((
        select permissions {
            id,
            name,
            code,
            description,
            roles: { id, code, name },
            application: { name },
            tags: { name },
            is_deleted,
        }
        offset (page - 1) * per_page
        limit per_page
    ))
};
