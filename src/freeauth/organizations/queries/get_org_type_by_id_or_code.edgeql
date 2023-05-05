WITH
    id := <optional uuid>$id,
    code := <optional str>$code
SELECT assert_single(
    (
        SELECT OrganizationType {
            name,
            code,
            description,
            is_deleted,
            is_protected
        }
        FILTER (.id = id) ?? (.code = code)
    )
);
