SELECT (
    UPDATE User FILTER .id = <uuid>$id
    SET {
        directly_organizations := (
            SELECT Organization
            FILTER .id IN array_unpack(<array<uuid>>$organization_ids)
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
