WITH
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    is_deleted := <optional bool>$is_deleted,
    organization_ids := <optional array<uuid>>$organization_ids,
    role := assert_single((
        SELECT Role
        FILTER
            (.id = id) ??
            (.code_upper ?= str_upper(current_code)) ??
            false
    ))
SELECT (
    UPDATE role
    SET {
        name := <str>$name,
        code := <optional str>$code,
        description := <optional str>$description,
        deleted_at := (
            .deleted_at IF NOT EXISTS is_deleted ELSE
            datetime_of_transaction() IF is_deleted ELSE {}
        ),
        organizations := (
            SELECT Organization
            FILTER .id IN array_unpack(organization_ids)
        )
    }
) {
    name,
    code,
    description,
    organizations: {
        code,
        name,
        is_org_type := EXISTS [is OrganizationType],
        is_enterprise := EXISTS [is Enterprise],
        is_department := EXISTS [is Department]
    },
    is_deleted,
    created_at
};
