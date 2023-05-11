SELECT
    User {
        name,
        username,
        email,
        mobile,
        org_type: { code, name },
        departments := (
            SELECT .directly_organizations { code, name }
        ),
        roles: { code, name },
        is_deleted,
        created_at,
        last_login_at
    }
FILTER .id = <uuid>$id;
