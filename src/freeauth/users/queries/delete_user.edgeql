SELECT (
    DELETE User FILTER .id in array_unpack(<array<uuid>>$user_ids)
) { name } ORDER BY .created_at DESC;
