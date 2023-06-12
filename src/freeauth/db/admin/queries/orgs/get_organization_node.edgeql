with
    module freeauth,
    ot_id := <optional uuid>$org_type_id,
    ot_code := <optional str>$org_type_code,
    parent_id := <optional uuid>$parent_id
select
    Organization {
        name,
        code,
        [is Department].description,
        parent_id := [is Department].parent.id,
        is_enterprise := Organization is Enterprise,
        has_children := exists .directly_children
    }
filter (
    [is Department].parent.id ?= parent_id if exists parent_id else
    [is Enterprise].org_type.id ?= ot_id if exists ot_id else
    ([is Enterprise].org_type.code = ot_code)
)
order by .created_at;
