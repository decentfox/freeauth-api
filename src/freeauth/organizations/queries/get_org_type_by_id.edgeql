SELECT
    OrganizationType { name, description, is_deleted, is_protected }
FILTER .id = <uuid>$id;
