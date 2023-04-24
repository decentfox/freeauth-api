WITH
    name := <optional str>$name,
    username := <str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    hashed_password := <str>$hashed_password
SELECT (
    INSERT User {
        name := name,
        username := username,
        email := email,
        mobile := mobile,
        hashed_password := hashed_password
    }
) {
    id, name, username, email, mobile,
    is_deleted, created_at, last_login_at
};
