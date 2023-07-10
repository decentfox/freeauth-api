with
    module freeauth,
    parent := (
        select Organization filter .id = <uuid>$parent_id
    ),
    enterprise := assert_single((
        select Enterprise filter (
            .id = (
                # https://github.com/edgedb/edgedb/issues/5474
                # parent[is Enterprise].id ??
                parent[is Enterprise].id if exists parent[is Enterprise] else
                parent[is Department].enterprise.id
            )
        )
    ))
for _ in (
    select true filter exists parent
) union (
    select (
        insert Department {
            name := <str>$name,
            code := <optional str>$code,
            description := <optional str>$description,
            enterprise := enterprise,
            parent := parent,
            ancestors := distinct (parent union parent.ancestors)
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
