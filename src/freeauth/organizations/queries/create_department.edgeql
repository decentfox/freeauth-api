WITH
    parent := (
        SELECT Organization FILTER .id = <uuid>$parent_id
    ),
    enterprise := assert_single((
        SELECT Enterprise FILTER (
            .id = (
                parent[is Enterprise].id ??
                parent[is Department].enterprise.id
            )
        )
    ))
FOR _ IN (
    SELECT true FILTER EXISTS parent
) UNION (
    SELECT (
        INSERT Department {
            name := <str>$name,
            code := <optional str>$code,
            description := <optional str>$description,
            enterprise := enterprise,
            parent := parent,
            ancestors := (
                SELECT DISTINCT (
                    SELECT
                        .parent UNION
                        .parent[is Department].ancestors
                )
            )
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
    }
);
