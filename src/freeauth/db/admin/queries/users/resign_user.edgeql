select (
    with is_deleted := <optional bool>$is_deleted,
    update freeauth::User filter .id in array_unpack(<array<uuid>>$user_ids)
    set {
        directly_organizations := {},
        org_type := {},
        roles := {},
        deleted_at := (
            datetime_of_transaction() if is_deleted else .deleted_at
        )
    }
) { name } order by .created_at desc;
