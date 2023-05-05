WITH
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    name := <optional str>$name,
    code := <optional str>$code,
    description := <optional str>$description,
    is_deleted := <optional bool>$is_deleted,
    org_type := assert_single((
        SELECT OrganizationType
        FILTER (.id = id) ?? (.code = code)
    ))
SELECT (
    UPDATE org_type
    SET {
        name := name ?? .name,
        code := code ?? .code,
        description := description ?? .description,
        deleted_at := (
            .deleted_at IF NOT EXISTS is_deleted ELSE
            datetime_of_transaction()
            IF is_deleted AND NOT .is_protected ELSE {}
        )
    }
) { name, code, description, is_deleted, is_protected };
