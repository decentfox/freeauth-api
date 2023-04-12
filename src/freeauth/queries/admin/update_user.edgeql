with
    username := <optional str>$username,
    email := <optional str>$email,
    hashed_password := <optional str>$hashed_password
select (
    update User filter .id = <uuid>$id
    set {
        username := username,
        email := email,
        hashed_password := hashed_password
    }
) {id, username, email, created_at};
