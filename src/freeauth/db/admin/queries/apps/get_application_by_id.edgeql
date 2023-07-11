with
    id := <uuid>$id,
select assert_single(
    (
        select freeauth::Application {
            name,
            description,
            is_deleted,
            is_protected,
            created_at
        }
        filter .id = id
    )
);
