select (
    for tag in enumerate(array_unpack(<array<uuid>>$ids))
    union (
        update PermissionTag filter .id = tag.1
        set {
            rank := tag.0 + 1
        }
    )
) {
    name,
    rank,
    created_at
}
