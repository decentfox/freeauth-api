with
    module freeauth,
    user_ids := <array<uuid>>$user_ids,
    role_ids := <array<uuid>>$role_ids,
    users := ( select User filter .id in array_unpack(user_ids) ),
    protected_admin_roles := (
        select Role
        filter .id in array_unpack(role_ids)
        and (
            select Permission
            filter .application.is_protected
            and .code = '*'
        ) in .permissions
        and not exists (
            ( select .users filter not .is_deleted )
            except users
        )
    )
select {
    unbind_users := array_agg((
        update users
        set {
            roles -= (
                select Role
                filter .id in array_unpack(role_ids)
                and Role not in protected_admin_roles
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
    }),
    protected_admin_roles := array_agg((
        select protected_admin_roles {
            name,
            code,
            description,
            org_type: {
                code,
                name,
            },
            is_deleted,
            created_at
        }
    ))
};
