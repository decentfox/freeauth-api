WITH
    id := <optional uuid>$id,
    code := <optional str>$code,
    enterprise_id := <optional uuid>$enterprise_id,
    enterprise_code := <optional str>$enterprise_code
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
        FILTER (
            .id = id IF EXISTS id ELSE (
                .code ?= code AND
                .enterprise.id = enterprise_id
            ) IF EXISTS enterprise_id ELSE (
                .code ?= code AND
                .enterprise.code = enterprise_code
            )
        )
    )
);
