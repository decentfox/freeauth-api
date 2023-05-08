SELECT (
    WITH is_deleted := <optional bool>$is_deleted,
    UPDATE User FILTER .id in array_unpack(<array<uuid>>$user_ids)
    SET {
        directly_organizations := {},
        deleted_at := datetime_of_transaction() IF is_deleted ELSE .deleted_at
    }
) { name } ORDER BY .created_at DESC;
