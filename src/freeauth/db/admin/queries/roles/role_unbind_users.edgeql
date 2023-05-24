WITH
    user_ids := <array<uuid>>$user_ids,
    role_ids := <array<uuid>>$role_ids
SELECT (
    UPDATE User FILTER .id in array_unpack(user_ids)
    SET {
        roles -= (
            SELECT Role
            FILTER .id IN array_unpack(role_ids)
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
