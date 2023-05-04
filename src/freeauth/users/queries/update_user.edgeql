WITH
    name := <optional str>$name,
    username := <optional str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    organization_ids := <optional array<uuid>>$organization_ids
SELECT (
    UPDATE User FILTER .id = <uuid>$id
    SET {
        name := name,
        username := username,
        email := email,
        mobile := mobile,
        org_branches := (
            SELECT Organization
            FILTER .id IN array_unpack(
                organization_ids ?? <array<uuid>>[]
            )
        )
    }
) {
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
};
