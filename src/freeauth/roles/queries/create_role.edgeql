SELECT (
    INSERT Role {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        organizations := (
            SELECT Organization
            FILTER .id IN array_unpack(
                <optional array<uuid>>$organization_ids
            )
        )
    }
) {
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
};
