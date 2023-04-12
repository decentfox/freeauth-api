select
    User {id, username, email, created_at}
filter .id = <uuid>$id;
