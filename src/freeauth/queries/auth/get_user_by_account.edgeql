WITH
    account := <str>$account,
    hashed_password := <optional str>$hashed_password
SELECT
    User {
        id, name, username, email, mobile,
        is_deleted, created_at, last_login_at
    }
FILTER
    (
        .username ?= account OR .email ?= account OR .mobile ?= account
    )
    AND
    (
        true IF NOT EXISTS hashed_password ELSE
        .hashed_password ?= hashed_password
    )
LIMIT 1;
