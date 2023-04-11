with
    username := <str>$username,
    email := <str>$email,
    hashed_password := <str>$hashed_password
select (
    update User filter .id = <uuid>$id
    set {
        username := username,
        email := email,
        hashed_password := hashed_password
    }
) {id, username, email};
