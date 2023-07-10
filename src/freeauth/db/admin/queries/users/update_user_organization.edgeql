with
    module freeauth,
    user := ( select User filter .id = <uuid>$id ),
    org_type_id := <optional uuid>$org_type_id,
    org_type := (
        user.org_type ?? (
            select OrganizationType filter .id = org_type_id
        )
    )
select (
    update user filter .id = <uuid>$id
    set {
        directly_organizations := (
            select Organization
            filter
                ( Organization is not OrganizationType )
                and (
                    false if not exists org_type else
                    (
                        .id in array_unpack(
                            <array<uuid>>$organization_ids
                        )
                        and org_type in .ancestors
                    )
                )
        ),
        org_type := org_type
    }
) {
    name,
    username,
    email,
    mobile,
    org_type: { code, name },
    departments := (
        select .directly_organizations { code, name }
    ),
    roles: { code, name },
    is_deleted,
    created_at,
    last_login_at
};
