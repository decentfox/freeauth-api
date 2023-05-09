WITH
    q := <optional str>$q,
    role_type := <optional str>$role_type,
    is_deleted := <optional bool>$is_deleted,
    organization := (
        SELECT Organization FILTER .id = <uuid>$org_id
    ),
    roles := (
        SELECT DISTINCT ((
            SELECT Role FILTER NOT EXISTS .organizations
        ) UNION (
            SELECT organization.<organizations[is Role]
        ) UNION (
            SELECT organization.ancestors.<organizations[is Role]
        ))
    )
SELECT roles {
    name,
    code,
    description,
    is_deleted,
    created_at,
    is_global_role := NOT EXISTS .organizations,
    is_org_type_role := EXISTS .organizations[is OrganizationType],
    is_enterprise_role := EXISTS .organizations[is Enterprise],
    is_department_role := EXISTS .organizations[is Department]
}
FILTER
    (
        true IF not EXISTS q ELSE
        .name ILIKE q OR
        .code ?? '' ILIKE q OR
        .description ?? '' ILIKE q
    ) AND (
        true IF NOT EXISTS role_type ELSE
        NOT EXISTS .organizations IF role_type = 'global' ELSE
        EXISTS .organizations[is OrganizationType]
        IF role_type = 'org_type' ELSE
        EXISTS .organizations[is Enterprise]
        IF role_type = 'enterprise' ELSE
        EXISTS .organizations[is Department]
        IF role_type = 'department' ELSE false
    ) AND (
        true IF NOT EXISTS is_deleted ELSE .is_deleted = is_deleted
    )
ORDER BY
    .is_deleted THEN
    .created_at DESC;
