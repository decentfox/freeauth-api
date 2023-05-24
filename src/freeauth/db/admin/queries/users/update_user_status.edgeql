WITH
    user_ids := <array<uuid>>$user_ids,
    is_deleted := <bool>$is_deleted
SELECT (
    UPDATE User FILTER .id in array_unpack(user_ids)
    SET {
        deleted_at := datetime_of_transaction() if is_deleted else {}
    }
) {
    name,
    is_deleted
} ORDER BY .created_at DESC;
