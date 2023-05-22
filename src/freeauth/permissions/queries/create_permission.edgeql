with
    name := <str>$name,
    code := <str>$code,
    description := <optional str>$description,
    application_id := <uuid>$application_id,
    new_tags := (
        for item in array_unpack(<array<str>>$new_tags) union (
            insert Tag {
                name := item,
                tag_type := TagType.Permission
            }
        )
    ),
    existing_tags := (
        select Tag
        filter .id in array_unpack(<array<uuid>>$existing_tag_ids)
    )
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
        tags := new_tags union existing_tags
    }
) {
    name,
    code,
    description,
    application: { name },
    tags: { name },
    is_deleted,
    created_at
}
