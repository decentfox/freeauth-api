with
    module freeauth
select
    User {
        name,
        username,
        email,
        mobile,
        org_type: { code, name },
        departments := (
            select .directly_organizations {
                id,
                code,
                name,
                enterprise := assert_single(.ancestors {
                    id,
                    name
                } filter exists [is Enterprise]),
                org_type := assert_single(.ancestors {
                    id,
                    name
                } filter exists [is OrganizationType])
            }
        ),
        roles: {
            name,
            code,
            description,
            org_type: { code, name },
            is_deleted,
            is_protected,
            created_at
        },
        is_deleted,
        created_at,
        last_login_at
    }
filter .id = <uuid>$id;
