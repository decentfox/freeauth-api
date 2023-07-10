with
    name := <str>$name,
    username := <str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile
select (
    update freeauth::User filter .id = <uuid>$id
    set {
        name := name,
        username := username,
        email := email,
        mobile := mobile
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
