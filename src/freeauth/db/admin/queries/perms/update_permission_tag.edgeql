with
    id := <uuid>$id,
    name := <str>$name,
select (
    update freeauth::PermissionTag filter .id = id
    set {
        name := name
    }
) {
    name,
    rank,
    created_at
};
