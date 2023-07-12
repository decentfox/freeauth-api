with
    module freeauth,
    role_ids := <array<uuid>>$role_ids,
    permission_ids := <array<uuid>>$permission_ids
select (
    update Role filter .id in array_unpack(role_ids)
    set {
        permissions += (
            select Permission
            filter .id in array_unpack(permission_ids)
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
    is_protected,
    created_at
};
