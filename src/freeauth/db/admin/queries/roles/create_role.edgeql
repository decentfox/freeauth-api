with
    module freeauth
select (
    insert Role {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        org_type := (
            select OrganizationType
            filter .id = <optional uuid>$org_type_id
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
