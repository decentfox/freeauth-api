with
    module freeauth,
    user := (
        update User
        filter
            .id = <uuid>$id and not .is_deleted
        set {
            name := <str>$name,
            username := <str>$username,
            email := <optional str>$email,
            mobile := <optional str>$mobile
        }
    ),
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
    is_deleted,
    created_at,
    last_login_at
};
