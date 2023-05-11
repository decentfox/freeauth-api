SELECT (
    INSERT Role {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        org_type := (
            SELECT OrganizationType
            FILTER .id = <optional uuid>$org_type_id
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
