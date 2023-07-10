with
    ids := <array<uuid>>$ids,
    is_deleted := <bool>$is_deleted
select (
    update freeauth::Permission filter .id in array_unpack(ids)
    set {
        deleted_at := datetime_of_transaction() if is_deleted else {}
    }
) { name, code, is_deleted };
