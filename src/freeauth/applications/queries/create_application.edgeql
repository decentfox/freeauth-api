select (
    insert Application {
        name := <str>$name,
        description := <optional str>$description,
    }
) {
    name,
    description,
    secret_key,
    is_deleted,
    created_at
}
