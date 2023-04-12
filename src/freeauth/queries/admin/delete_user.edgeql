with
    user := (delete User filter .id = <uuid>$id)
select
    User {id, username};
