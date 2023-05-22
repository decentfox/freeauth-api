WITH
    username := <optional str>$username,
    mobile := <optional str>$mobile,
    email := <optional str>$email
SELECT
    User { id, is_deleted }
FILTER (
    .username ?= username IF EXISTS username ELSE
    .mobile ?= mobile IF EXISTS mobile ELSE
    .email ?= email IF EXISTS email ELSE false
)
LIMIT 1;
