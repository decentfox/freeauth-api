select (
    update freeauth::User filter .id = <uuid>$id set {
        hashed_password := <str>$hashed_password
    }
) {
    username,
    email
}
