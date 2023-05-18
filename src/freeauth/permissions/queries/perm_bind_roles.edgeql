with
    role_ids := <array<uuid>>$role_ids,
    permission_id := <uuid>$permission_id
select (
    update Role filter .id in array_unpack(role_ids)
    set {
        permissions += (
            select Permission filter .id = permission_id
        )
    }
) {
    name,
    code,
    description,
    org_type: {
        code,
        name,
    },
    is_deleted,
    created_at
};
