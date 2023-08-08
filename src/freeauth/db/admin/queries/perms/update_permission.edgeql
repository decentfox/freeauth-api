with
    module freeauth,
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
                insert PermissionTag {
                    name := item,
                } unless conflict on .name
                else (
                    select PermissionTag filter .name = item
                )
            )
        ),
        deleted_at := (
            .deleted_at if not exists is_deleted else
            datetime_of_transaction() if is_deleted else {}
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
};
