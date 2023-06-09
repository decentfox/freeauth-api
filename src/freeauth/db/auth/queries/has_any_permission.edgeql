with
    perm_codes := str_upper(array_unpack(<array<str>>$perm_codes)),
    wildcard_perm := (
        select Permission
        filter
            .application = global current_app
            and .code = '*'
    ),
    user_perms := (
        select global current_user.permissions
        filter .application = global current_app
    )
select any({
    any(user_perms.code_upper in perm_codes),
    wildcard_perm in user_perms
});
