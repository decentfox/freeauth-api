with
    username := <optional str>$username,
    mobile := <optional str>$mobile,
    email := <optional str>$email
select
    freeauth::User { id, is_deleted }
filter (
    .username ?= username if exists username else
    .mobile ?= mobile if exists mobile else
    .email ?= email if exists email else false
)
limit 1;
