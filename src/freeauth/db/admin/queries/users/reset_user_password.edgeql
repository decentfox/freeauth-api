select (
    update freeauth::User filter .id = <uuid>$id set {
        reset_pwd_on_next_login := <bool>$reset_pwd_on_next_login,
        hashed_password := <str>$hashed_password
    }
) {
    username,
    email
}
