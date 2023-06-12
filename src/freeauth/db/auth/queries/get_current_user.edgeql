with
    module freeauth,
    user := global current_user,
    perms := (
        select user.permissions
        filter .application = global current_app
    )
select user {
    name,
    username,
    email,
    mobile,
    org_type: { code, name },
    departments := (
        select .directly_organizations { code, name }
    ),
    roles: { code, name },
    perms := array_agg(perms.code),
    is_deleted,
    created_at,
    last_login_at,
    reset_pwd_on_next_login
};
