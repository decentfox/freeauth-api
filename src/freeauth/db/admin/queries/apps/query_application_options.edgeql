with
    q := <optional str>$q
select Application {
    id,
    name,
    description,
    is_deleted,
    is_protected
} filter
    true if not exists q else
    .name ilike q or
    .description ?? '' ilike q
order by .created_at desc;
