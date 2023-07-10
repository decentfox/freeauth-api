select (
    update freeauth::Role
    filter .id in array_unpack(<array<uuid>>$ids)
    set {
        deleted_at := (
            datetime_of_transaction() if <bool>$is_deleted else {}
        )
    }
) { name, code, is_deleted };
