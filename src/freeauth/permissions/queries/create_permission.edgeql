select (
    insert Permission {
        name := <str>$name,
        code := <str>$code,
        description := <optional str>$description,
        application := (
            select Application filter (
                .id = <uuid>$application_id
            )
        )
    }
) {
    name,
    code,
    description,
    application: { name },
    is_deleted,
    created_at
}
