SELECT (
    UPDATE User FILTER .id in array_unpack(<array<uuid>>$user_ids)
    SET {
        directly_organizations := {},
        deleted_at := datetime_of_transaction()
    }
) { name } ORDER BY .created_at DESC;
