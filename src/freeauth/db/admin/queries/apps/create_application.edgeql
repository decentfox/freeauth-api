with
    module freeauth,
    app := (
        insert Application {
            name := <str>$name,
            description := <optional str>$description,
            hashed_secret := <str>$hashed_secret
        }
    ),
    wildcard_perm := (
        insert Permission {
            name := '通配符权限',
            code := '*',
            description := '通配符权限授予应用的所有访问权限',
            application := app
        }
    )
select app {
    name,
    description,
    is_deleted,
    created_at
}
