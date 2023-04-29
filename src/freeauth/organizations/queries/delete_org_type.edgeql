SELECT (
    DELETE OrganizationType
    FILTER .id in array_unpack(<array<uuid>>$ids)
) { name };
