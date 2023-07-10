with
    id := <uuid>$id,
    name := <str>$name,
select (
    update PermissionTag filter .id = id
    set {
        name := name
    }
) { 
    name,
    rank,
    created_at
};
