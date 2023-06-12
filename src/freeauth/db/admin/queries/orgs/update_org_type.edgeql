with
    module freeauth,
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    name := <optional str>$name,
    code := <optional str>$code,
    description := <optional str>$description,
    is_deleted := <optional bool>$is_deleted,
    org_type := assert_single((
        select OrganizationType
        filter (.id = id) ?? (.code = code)
    ))
select (
    update org_type
    set {
        name := name ?? .name,
        code := code ?? .code,
        description := description ?? .description,
        deleted_at := (
            .deleted_at if not exists is_deleted else
            datetime_of_transaction()
            if is_deleted and not .is_protected else {}
        )
    }
) { name, code, description, is_deleted, is_protected };
