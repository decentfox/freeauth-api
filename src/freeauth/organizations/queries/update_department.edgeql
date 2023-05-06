WITH
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    enterprise_id := <optional uuid>$enterprise_id,
    parent := (
        SELECT Organization FILTER .id = <uuid>$parent_id
    ),
    parent_is_enterprise := EXISTS parent[is Enterprise],
    enterprise := assert_single((
        SELECT Enterprise FILTER .id = (
            parent[is Enterprise].id IF parent_is_enterprise ELSE
            parent[is Department].enterprise.id
        )
    )),
    department := assert_single((
        SELECT Department
        FILTER
            (.id = id) ??
            (
                .code ?= current_code AND
                .enterprise.id = enterprise_id
            ) ??
            false
    ))
SELECT (
    UPDATE department
    SET {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        enterprise := enterprise,
        parent := parent
    }
) {
    name,
    code,
    description,
    parent: {
        name,
        code
    },
    enterprise: {
        name,
        code,
    }
};
