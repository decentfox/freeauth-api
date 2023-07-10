with
    name := <str>$name,
select (
    insert freeauth::PermissionTag {
        name := name,
    }
) {
    name,
    rank,
    created_at
}
