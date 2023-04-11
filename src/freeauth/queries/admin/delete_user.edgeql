with
    user := (delete User filter .id = <uuid>$id)
select
    user {id, username};
