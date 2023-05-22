WITH
    id := <optional uuid>$id,
    code := <optional str>$code,
    enterprise_id := <optional uuid>$enterprise_id
SELECT assert_single(
    (
        SELECT Department {
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
        FILTER
            (.id = id) ??
            (.code ?= code AND .enterprise.id = enterprise_id)
    )
);
