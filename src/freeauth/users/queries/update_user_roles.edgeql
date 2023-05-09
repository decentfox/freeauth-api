WITH
    user_id := <uuid>$id,
    role_ids := <optional array<uuid>>$role_ids
SELECT (
    UPDATE User FILTER .id = user_id
    SET {
        roles := (
            SELECT Role
            FILTER .id IN array_unpack(role_ids)
        )
    }
) {
    name,
    username,
    email,
    mobile,
    departments := (
        SELECT .directly_organizations { id, code, name }
    ),
    roles := (
        SELECT .roles { id, code, name }
    ),
    is_deleted,
    created_at,
    last_login_at
};
