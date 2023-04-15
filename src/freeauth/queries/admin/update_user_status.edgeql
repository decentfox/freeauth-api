with
    user_ids := <array<uuid>>$user_ids,
    is_deleted := <bool>$is_deleted
select (
    update User filter .id in array_unpack(user_ids)
    set {
        deleted_at := datetime_of_transaction() if is_deleted else {}
    }
) {
    id, name, is_deleted
} order by .created_at desc;
