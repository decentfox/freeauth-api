SELECT
    User {
        name,
        username,
        email,
        mobile,
        departments := (
            SELECT .org_branches { code, name }
        ),
        is_deleted,
        created_at,
        last_login_at
    }
FILTER .id = <uuid>$id;
