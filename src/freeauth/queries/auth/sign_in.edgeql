SELECT (
    UPDATE User
    FILTER .id = <uuid>$id
    SET { last_login_at := datetime_of_transaction() }
) {
    id, name, username, email, mobile,
    is_deleted, created_at, last_login_at
};
