with
    id := <optional uuid>$id,
    code := <optional str>$code
select assert_single(
    (
        select freeauth::OrganizationType {
            name,
            code,
            description,
            is_deleted,
            is_protected
        }
        filter (.id = id) ?? (.code = code)
    )
);
