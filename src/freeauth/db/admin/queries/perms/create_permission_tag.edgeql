with
    name := <str>$name,
select (
    insert PermissionTag {
        name := name,
    }
) {
    name,
    rank,
    created_at
}
