WITH
    account := <str>$account
SELECT
    User { id, hashed_password, is_deleted }
FILTER .username ?= account OR .email ?= account OR .mobile ?= account
LIMIT 1;
