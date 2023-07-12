with
    is_deleted := <bool>$is_deleted
select (
    update freeauth::Application
    filter .id in array_unpack(<array<uuid>>$ids) and not .is_protected
    set {
        deleted_at := datetime_of_transaction() if is_deleted else {}
    }
) { name, is_deleted };
