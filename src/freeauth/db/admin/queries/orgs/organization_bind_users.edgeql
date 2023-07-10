with
    module freeauth,
    user_ids := <array<uuid>>$user_ids,
    organization_ids := <array<uuid>>$organization_ids,
    org_type := (
        select OrganizationType filter (
            .id = <uuid>$org_type_id
        )
    ),
    organizations := (
        select Organization
        filter
            ( Organization is not OrganizationType ) and
            (
                false if not exists org_type else
                (
                    .id in array_unpack(organization_ids) and
                    org_type in .ancestors
                )
            )
    )
select (
    update User filter
        .id in array_unpack(user_ids) and
        (
            not exists .org_type or
            .org_type ?= org_type
        )
    set {
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
        select .directly_organizations { code, name }
    ),
    roles: { code, name },
    is_deleted,
    created_at,
    last_login_at
};
