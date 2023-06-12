with
    module freeauth,
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    enterprise_id := <optional uuid>$enterprise_id,
    parent := (
        select Organization filter .id = <uuid>$parent_id
    ),
    parent_is_enterprise := exists parent[is Enterprise],
    enterprise := assert_single((
        select Enterprise filter .id = (
            parent[is Enterprise].id if parent_is_enterprise else
            parent[is Department].enterprise.id
        )
    )),
    department := assert_single((
        select Department
        filter
            (.id = id) ??
            (
                .code ?= current_code and
                .enterprise.id = enterprise_id
            ) ??
            false
    ))
select (
    update department
    set {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        enterprise := enterprise,
        parent := parent,
        ancestors := (
            select distinct (
                select .parent union .parent.ancestors
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
};
