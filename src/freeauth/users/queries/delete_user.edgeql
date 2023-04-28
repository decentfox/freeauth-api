select (
    delete User filter .id in array_unpack(<array<uuid>>$user_ids)
) {id, name} order by .created_at desc;
