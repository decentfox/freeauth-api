select (
    delete freeauth::User filter .id in array_unpack(<array<uuid>>$user_ids)
) { name } order by .created_at desc;
