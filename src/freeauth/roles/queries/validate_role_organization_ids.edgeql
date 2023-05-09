WITH
    organization_ids := array_unpack(<array<uuid>>$organization_ids),
    organizations := (
        SELECT Organization FILTER .id IN organization_ids
    ),
    children := (
        SELECT DISTINCT (
            FOR x IN organizations
            UNION (
                SELECT x.children
            )
        )
    ),
    invalid_organizations := (
        SELECT organizations FILTER organizations IN children
    )
SELECT array_agg(invalid_organizations.name);
