SELECT (
    DELETE OrganizationType
    FILTER .id in array_unpack(<array<uuid>>$ids) AND NOT .is_protected
) { name, code };
