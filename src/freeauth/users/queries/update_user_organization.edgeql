SELECT (
    UPDATE User FILTER .id = <uuid>$id
    SET {
        directly_organizations := (
            SELECT Organization
            FILTER
                ( Organization IS NOT OrganizationType ) AND
                (
                    false IF NOT EXISTS User.org_type ELSE
                    (
                        .id IN array_unpack(
                            <array<uuid>>$organization_ids
                        ) AND
                        User.org_type IN .ancestors
                    )
                )
        )
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
