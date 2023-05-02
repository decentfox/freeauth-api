WITH
    parent := (
        SELECT Organization FILTER .id = <uuid>$parent_id
    ),
    parent_is_enterprise := EXISTS parent[is Enterprise],
    enterprise := assert_single((
        SELECT Enterprise FILTER (
            .id = parent[is Enterprise].id IF parent_is_enterprise ELSE
            .id = parent[is Department].enterprise.id
        )
    ))
SELECT (
    UPDATE Department
    FILTER .id = <uuid>$id
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
    }
};
