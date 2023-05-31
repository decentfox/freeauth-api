for code in array_unpack(<array<str>>$perm_codes)
union (
    insert Permission {
        name := code,
        code := code,
        application := global current_app
    } unless conflict
);
