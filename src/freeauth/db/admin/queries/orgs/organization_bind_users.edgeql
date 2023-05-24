WITH
    user_ids := <array<uuid>>$user_ids,
    organization_ids := <array<uuid>>$organization_ids,
    org_type := (
        SELECT OrganizationType FILTER (
            .id = <uuid>$org_type_id
        )
    ),
    organizations := (
        SELECT Organization
        FILTER
            ( Organization IS NOT OrganizationType ) AND
            (
                false IF NOT EXISTS org_type ELSE
                (
                    .id IN array_unpack(organization_ids) AND
                    org_type IN .ancestors
                )
            )
    )
SELECT (
    UPDATE User FILTER
        .id in array_unpack(user_ids) AND
        (
            NOT EXISTS .org_type OR
            .org_type ?= org_type
        )
    SET {
        org_type := org_type,
        directly_organizations += organizations
    }
) {
    name,
    username,
    email,
    mobile,
    org_type: { code, name },
    departments := (
        SELECT .directly_organizations { code, name }
    ),
    roles: { code, name },
    is_deleted,
    created_at,
    last_login_at
};
