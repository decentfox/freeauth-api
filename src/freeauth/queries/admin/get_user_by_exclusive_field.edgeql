WITH
    id := <optional uuid>$id,
    username := <optional str>$username,
    mobile := <optional str>$mobile,
    email := <optional str>$email
SELECT
    User {
        id, name, username, email, mobile,
        is_deleted, created_at, last_login_at
    }
FILTER (
    (
        true IF NOT EXISTS id ELSE .id = id
    )
    AND
    (
        true IF NOT EXISTS username ELSE .username = username
    )
    AND
    (
        true IF NOT EXISTS mobile ELSE .mobile = mobile
    )
    AND
    (
        true IF NOT EXISTS email ELSE .email = email
    )
    AND (EXISTS id OR EXISTS username OR EXISTS mobile OR EXISTS email)
) LIMIT 1
