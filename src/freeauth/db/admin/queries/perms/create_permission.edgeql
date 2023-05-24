with
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
                insert Tag {
                    name := item,
                    tag_type := TagType.Permission
                } unless conflict on .name
                else (
                    select Tag filter .name = item and .tag_type = TagType.Permission
                )
            )
        )
    }
) {
    name,
    code,
    description,
    roles: { name },
    application: { name },
    tags: { name },
    is_deleted,
    created_at
}
