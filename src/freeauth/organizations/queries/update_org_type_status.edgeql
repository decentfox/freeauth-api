WITH
    is_deleted := <bool>$is_deleted
SELECT (
    UPDATE OrganizationType
    FILTER .id in array_unpack(<array<uuid>>$ids) AND NOT .is_protected
    SET {
        deleted_at := datetime_of_transaction() IF is_deleted ELSE {}
    }
) { name, code, is_deleted };
