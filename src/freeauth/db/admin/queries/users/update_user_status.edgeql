with
    module freeauth,
    user_ids := <array<uuid>>$user_ids,
    is_deleted := <bool>$is_deleted,
    users := ( select User filter .id in array_unpack(user_ids) ),
    protected_admin_roles := (
        select Role
        filter .is_protected
        and is_deleted
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
    users := (
        update users except protected_admin_users
        set {
            deleted_at := datetime_of_transaction() if is_deleted else {}
        }
    ) {
        name,
        is_deleted
    },
    protected_admin_users := (
        select protected_admin_users {
            name,
            is_deleted
        }
    ),
    protected_admin_roles := (
        select protected_admin_roles { name }
    )
};
