WITH
    access_token := <str>$access_token,
    user := (
        UPDATE User
        FILTER .id = <uuid>$id
        SET { last_login_at := datetime_of_transaction() }
    ),
    token := (
        INSERT auth::Token {
            access_token := access_token,
            user := user
        }
    )
SELECT user {
    id, name, username, email, mobile,
    is_deleted, created_at, last_login_at
};
