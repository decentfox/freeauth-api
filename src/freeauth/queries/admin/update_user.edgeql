with
    name := <optional str>$name,
    username := <optional str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    hashed_password := <optional str>$hashed_password
select (
    update User filter .id = <uuid>$id
    set {
        name := name,
        username := username,
        email := email,
        mobile := mobile,
        hashed_password := hashed_password
    }
) {
    id, name, username, email, mobile,
    is_deleted, created_at, last_login_at
};
