WITH
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    is_deleted := <optional bool>$is_deleted,
    role := assert_single((
        SELECT Role
        FILTER
            (.id = id) ??
            (.code_upper ?= str_upper(current_code)) ??
            false
    ))
SELECT (
    UPDATE role
    SET {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        deleted_at := (
            .deleted_at IF NOT EXISTS is_deleted ELSE
            datetime_of_transaction() IF is_deleted ELSE {}
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
