WITH
    name := <str>$name,
    description := <optional str>$description
SELECT (
    INSERT OrganizationType {
        name := name,
        description := description
    }
) { name, description, is_deleted, is_protected };
