with
    id := <optional uuid>$id,
    code := <optional str>$code
select assert_single(
    (
        select freeauth::Role {
            name,
            code,
            description,
            org_type: {
                code,
                name,
            },
            is_deleted,
            is_protected,
            created_at
        }
        filter (.id = id) ?? (.code_upper = str_upper(code))
    )
);
