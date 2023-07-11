with
    module freeauth,
    user_ids := <array<uuid>>$user_ids,
    is_deleted := <bool>$is_deleted,
    users := ( select User filter .id in array_unpack(user_ids) ),
    protected_admin_roles := (
        select Role
        filter (
            select Permission
            filter .application.is_protected
            and .code = '*'
        ) in .permissions
        and not exists (
            ( select .users filter not .is_deleted )
            except users
        )
    ),
    protected_admin_users := (
        select users
        filter
            exists protected_admin_roles
            and users.roles in protected_admin_roles
    )
select {
    users := array_agg((
        update users except protected_admin_users
        set {
            deleted_at := datetime_of_transaction() if is_deleted else {}
        }
    ) {
        name,
        is_deleted
    }),
    protected_admin_users := array_agg((
        select protected_admin_users {
            name,
            is_deleted
        }
    )),
    protected_admin_roles := array_agg((
        select protected_admin_roles { name }
    ))
};
