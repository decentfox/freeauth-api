select freeauth::PermissionTag {
    id,
    name
} order by .rank then .created_at
