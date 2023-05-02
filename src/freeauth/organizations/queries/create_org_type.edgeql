WITH
    name := <str>$name,
    code := <str>$code,
    description := <optional str>$description
SELECT (
    INSERT OrganizationType {
        name := name,
        code := code,
        description := description
    }
) { name, code, description, is_deleted, is_protected };
