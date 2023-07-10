with
    id := <optional uuid>$id,
    code := <optional str>$code,
    enterprise_id := <optional uuid>$enterprise_id
select assert_single(
    (
        select freeauth::Department {
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
        filter
            (.id = id) ??
            (.code ?= code and .enterprise.id = enterprise_id)
    )
);
