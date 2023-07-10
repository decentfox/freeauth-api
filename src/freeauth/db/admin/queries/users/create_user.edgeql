with
    module freeauth,
    name := <optional str>$name,
    username := <optional str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    hashed_password := <optional str>$hashed_password,
    reset_pwd_on_first_login := <bool>$reset_pwd_on_first_login,
    organization_ids := <optional array<uuid>>$organization_ids,
    org_type := (
        select OrganizationType filter (
            .id = <optional uuid>$org_type_id
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
    insert User {
        name := name,
        username := username,
        email := email,
        mobile := mobile,
        hashed_password := hashed_password,
        org_type := org_type,
        directly_organizations := organizations,
        reset_pwd_on_next_login := reset_pwd_on_first_login
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
