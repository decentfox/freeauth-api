select freeauth::OrganizationType {
    name, code, description, is_deleted, is_protected
} order by
    .is_deleted then
    .is_protected desc then
    .code;
