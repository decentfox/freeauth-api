select global current_user {
    name,
    username,
    email,
    mobile,
    org_type: { code, name },
    departments := (
        select .directly_organizations { code, name }
    ),
    roles: { code, name },
    permissions := (
        select .permissions { code, name }
        filter .application = global current_app
    ),
    is_deleted,
    created_at,
    last_login_at
};
