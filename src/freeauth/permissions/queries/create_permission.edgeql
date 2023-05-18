select (
    insert Permission {
        name := <str>$name,
        code := <str>$code,
        description := <optional str>$description,
    }
) {
    name,
    code,
    description,
    is_deleted,
    created_at
}