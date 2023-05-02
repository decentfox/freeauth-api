WITH
    name := <optional str>$name,
    code := <optional str>$code,
    description := <optional str>$description,
    is_deleted := <optional bool>$is_deleted
SELECT (
    UPDATE OrganizationType
    FILTER .id = <uuid>$id
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
