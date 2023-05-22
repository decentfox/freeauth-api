WITH
    name := <optional str>$name,
    username := <optional str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    hashed_password := <optional str>$hashed_password,
    organization_ids := <optional array<uuid>>$organization_ids,
    org_type := (
        SELECT OrganizationType FILTER (
            .id = <optional uuid>$org_type_id
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
select (
    insert User {
        name := name,
        username := username,
        email := email,
        mobile := mobile,
        hashed_password := hashed_password,
        org_type := org_type,
        directly_organizations := organizations
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
