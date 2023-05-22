WITH
    ot_id := <optional uuid>$org_type_id,
    ot_code := <optional str>$org_type_code,
    parent_id := <optional uuid>$parent_id
SELECT
    Organization {
        name,
        code,
        [IS Department].description,
        parent_id := [IS Department].parent.id,
        is_enterprise := Organization is Enterprise,
        has_children := EXISTS .directly_children
    }
FILTER (
    [IS Department].parent.id ?= parent_id IF EXISTS parent_id ELSE
    [IS Enterprise].org_type.id ?= ot_id IF EXISTS ot_id ELSE
    ([IS Enterprise].org_type.code = ot_code)
)
ORDER BY .created_at;
