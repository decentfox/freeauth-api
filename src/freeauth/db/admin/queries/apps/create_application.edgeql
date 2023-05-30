select (
    insert Application {
        name := <str>$name,
        description := <optional str>$description,
        hashed_secret := <str>$hashed_secret
    }
) {
    name,
    description,
    secret := .hashed_secret,
    is_deleted,
    created_at
}
