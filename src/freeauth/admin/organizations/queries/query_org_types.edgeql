SELECT OrganizationType {
    name, code, description, is_deleted, is_protected
} ORDER BY
    .is_deleted THEN
    .is_protected DESC THEN
    .code;
