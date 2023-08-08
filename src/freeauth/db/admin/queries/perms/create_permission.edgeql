with
    module freeauth,
    name := <str>$name,
    code := <str>$code,
    description := <optional str>$description,
    application_id := <uuid>$application_id,
    tags := <optional array<str>>$tags
select (
    insert Permission {
        name := name,
        code := code,
        description := description,
        application := (
            select Application filter (
                .id = application_id
            )
        ),
        tags :=  (
            for item in array_unpack(tags) union (
                insert PermissionTag {
                    name := item,
                } unless conflict on .name
                else (
                    select PermissionTag filter .name = item
                )
            )
        )
    }
) {
    name,
    code,
    description,
    roles: { name },
    application: { name, is_protected },
    tags: { name },
    is_deleted,
    created_at
}
