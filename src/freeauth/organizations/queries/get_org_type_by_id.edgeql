SELECT
    OrganizationType {
        name,
        code,
        description,
        is_deleted,
        is_protected
    }
FILTER .id = <uuid>$id;
