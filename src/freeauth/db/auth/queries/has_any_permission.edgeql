with
    perm_codes := str_upper(array_unpack(<array<str>>$perm_codes)),
    user_perms := (
        select global current_user.permissions
        filter .application = global current_app
    )
select any(user_perms.code in perm_codes);
