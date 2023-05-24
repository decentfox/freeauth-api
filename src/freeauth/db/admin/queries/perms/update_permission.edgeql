with
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    is_deleted := <optional bool>$is_deleted,
    permission := assert_single((
        select Permission
        filter
            (.id = id) ??
            (.code_upper ?= str_upper(current_code)) ??
            false
    )),
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
    update permission
    set {
        name := <str>$name,
        code := <str>$code,
        description := <optional str>$description,
        tags := new_tags union existing_tags,
        deleted_at := (
            .deleted_at IF NOT EXISTS is_deleted ELSE
            datetime_of_transaction() IF is_deleted ELSE {}
        )
    }
) {
    name,
    code,
    description,
    roles: {
        id,
        name,
        code,
        description,
        is_deleted,
        created_at
    },
    application: { name },
    tags: { id, name },
    is_deleted,
    created_at
};
