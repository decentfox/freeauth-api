select
    User {
        id, name, username, email, mobile,
        is_deleted, created_at, last_login_at
    }
filter .id = <uuid>$id;
