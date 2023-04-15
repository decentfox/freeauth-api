with
    name := <optional str>$name,
    username := <optional str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
select (
    update User filter .id = <uuid>$id
    set {
        name := name,
        username := username,
        email := email,
        mobile := mobile,
    }
) {
    id, name, username, email, mobile,
    is_deleted, created_at, last_login_at
};
