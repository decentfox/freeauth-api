with
    name := <str>$name,
    description := <optional str>$description,
select (
    update freeauth::Application filter .id = <uuid>$id
    set {
        name := name,
        description := description,
    }
) {
    name,
    description,
    is_deleted,
    is_protected,
    created_at
};
