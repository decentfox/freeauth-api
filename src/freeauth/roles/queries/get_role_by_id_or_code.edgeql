WITH
    id := <optional uuid>$id,
    code := <optional str>$code
SELECT assert_single(
    (
        SELECT Role {
            name,
            code,
            description,
            org_type: {
                code,
                name,
            },
            is_deleted,
            created_at
        }
        FILTER (.id = id) ?? (.code_upper = str_upper(code))
    )
);
