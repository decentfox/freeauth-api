with
    module freeauth,
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    is_deleted := <optional bool>$is_deleted,
    role := assert_single((
        select Role
        filter
            (.id = id) ??
            (.code_upper ?= str_upper(current_code)) ??
            false
    ))
select (
    update role
    set {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        deleted_at := (
            .deleted_at if not exists is_deleted else
            datetime_of_transaction() if is_deleted else {}
        )
    }
) {
    name,
    code,
    description,
    org_type: {
        code,
        name,
    },
    is_deleted,
    created_at
};
