WITH
    id := <optional uuid>$id,
    code := <optional str>$code
SELECT assert_single(
    (
        SELECT Role {
            name,
            code,
            description,
            organizations: {
                code,
                name,
                is_org_type := EXISTS [is OrganizationType],
                is_enterprise := EXISTS [is Enterprise],
                is_department := EXISTS [is Department]
            },
            is_deleted,
            created_at
        }
        FILTER (.id = id) ?? (.code_upper = str_upper(code))
    )
);
