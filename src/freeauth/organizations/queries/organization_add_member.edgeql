WITH
    user_ids := <array<uuid>>$user_ids,
    organization_ids := <array<uuid>>$organization_ids
SELECT (
    UPDATE User FILTER .id in array_unpack(user_ids)
    SET {
        directly_organizations += (
            SELECT Organization
            FILTER .id IN array_unpack(organization_ids)
        )
    }
) {
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
};
