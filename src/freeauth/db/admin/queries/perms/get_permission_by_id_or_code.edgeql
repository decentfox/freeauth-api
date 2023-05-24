with
    id := <optional uuid>$id,
    code := <optional str>$code
select assert_single(
    (
        select Permission {
            name,
            code,
            description,
            roles: {
                id,
                name,
                code,
                description,
                is_deleted,
                created_at
            },
            application: { name },
            tags: { id, name },
            is_deleted,
            created_at
        }
        filter (.id = id) ?? (.code_upper = str_upper(code))
    )
);
