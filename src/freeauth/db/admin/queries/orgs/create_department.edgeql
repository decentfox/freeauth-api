WITH
    parent := (
        SELECT Organization FILTER .id = <uuid>$parent_id
    ),
    enterprise := assert_single((
        SELECT Enterprise FILTER (
            .id = (
                # https://github.com/edgedb/edgedb/issues/5474
                # parent[is Enterprise].id ??
                parent[is Enterprise].id if exists parent[is Enterprise] else

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
            ancestors := DISTINCT (parent UNION parent.ancestors)
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
