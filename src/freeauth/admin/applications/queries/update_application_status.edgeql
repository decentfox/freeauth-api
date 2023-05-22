with
    is_deleted := <bool>$is_deleted
select (
    update Application
    filter .id in array_unpack(<array<uuid>>$ids)
    SET {
        deleted_at := datetime_of_transaction() IF is_deleted ELSE {}
    }
) { name, is_deleted };
