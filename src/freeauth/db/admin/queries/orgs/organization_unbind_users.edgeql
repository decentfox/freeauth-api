with
    module freeauth,
    user_ids := <array<uuid>>$user_ids,
    organization_ids := <array<uuid>>$organization_ids,
    organizations := (
        select Organization
        filter .id in array_unpack(organization_ids)
    )
select (
    update User filter .id in array_unpack(user_ids)
    set {
        org_type := .org_type
        if array_agg(
            User.directly_organizations) != array_agg(organizations)
        else {},
        directly_organizations -= organizations,
        roles -= .org_type.roles
        if array_agg(
            User.directly_organizations) = array_agg(organizations)
        else {},
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
