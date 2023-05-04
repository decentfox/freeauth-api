with
    name := <optional str>$name,
    username := <optional str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    hashed_password := <optional str>$hashed_password,
    organization_ids := <optional array<uuid>>$organization_ids
select (
    insert User {
        name := name,
        username := username,
        email := email,
        mobile := mobile,
        hashed_password := hashed_password,
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
