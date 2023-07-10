with
    module freeauth,
    user_ids := <array<uuid>>$user_ids,
    role_ids := <array<uuid>>$role_ids
select (
    update User filter .id in array_unpack(user_ids)
    set {
        roles += (
            select Role
            filter
                .id IN array_unpack(role_ids) and
                (
                    not exists .org_type or
                    .org_type ?= User.org_type
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
        select .directly_organizations { code, name }
    ),
    roles: { code, name },
    is_deleted,
    created_at,
    last_login_at
};
