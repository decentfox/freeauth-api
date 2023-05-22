SELECT (
    UPDATE Role
    FILTER .id in array_unpack(<array<uuid>>$ids)
    SET {
        deleted_at := (
            datetime_of_transaction() IF <bool>$is_deleted ELSE {}
        )
    }
) { name, code, is_deleted };
