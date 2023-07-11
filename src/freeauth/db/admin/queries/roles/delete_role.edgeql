with
    module freeauth,
    wildcard_perm := (
        select Permission
        filter .application.is_protected
        and .code = '*'
    )
delete Role
filter .id in array_unpack(<array<uuid>>$ids)
and (
    true if not exists wildcard_perm else
    wildcard_perm not in .permissions
);
