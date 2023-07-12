with
    module freeauth,
    user_id := <uuid>$id,
    role_ids := <optional array<uuid>>$role_ids,
    user := ( select User filter .id = user_id ),
    roles := (
        select Role
        filter
            .id in array_unpack(role_ids) and
            (
                not exists .org_type or
                .org_type ?= user.org_type
            )
    ),
    deleted_roles := user.roles except roles,
    protected_admin_roles := (
        select deleted_roles
        filter .is_protected
        and not exists (
            ( select .users filter not .is_deleted )
            except user
        )
    )
select {
    user := (
        update user
        set {
            roles := roles union protected_admin_roles
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
    },
    protected_admin_roles := (
        select protected_admin_roles {
            name,
            code,
            description,
            org_type: {
                code,
                name,
            },
            is_deleted,
            is_protected,
            created_at
        }
    )
};
