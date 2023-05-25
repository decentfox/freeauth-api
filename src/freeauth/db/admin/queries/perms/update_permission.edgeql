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
    tags := <optional array<str>>$tags
select (
    update permission
    set {
        name := <str>$name,
        code := <str>$code,
        description := <optional str>$description,
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
        ),
        deleted_at := (
            .deleted_at IF NOT EXISTS is_deleted ELSE
            datetime_of_transaction() IF is_deleted ELSE {}
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
};
