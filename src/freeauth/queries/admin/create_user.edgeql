with
    username := <str>$username,
    email := <str>$email,
    hashed_password := <str>$hashed_password
select (
    insert User {
        username := username,
        email := email,
        hashed_password := hashed_password
    }
) {id, username, email};
