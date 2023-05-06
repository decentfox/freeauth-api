SELECT
    User {
        name,
        username,
        email,
        mobile,
        departments := (
            SELECT .directly_organizations { code, name }
        ),
        is_deleted,
        created_at,
        last_login_at
    }
FILTER .id = <uuid>$id;
