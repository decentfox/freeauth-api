WITH
    user_id := <uuid>$id,
    role_ids := <optional array<uuid>>$role_ids
SELECT (
    UPDATE User FILTER .id = user_id
    SET {
        roles := (
            SELECT Role
            FILTER
                .id IN array_unpack(role_ids) AND
                (
                    NOT EXISTS .org_type OR
                    .org_type ?= User.org_type
                )
        )
    }
) {
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
};
