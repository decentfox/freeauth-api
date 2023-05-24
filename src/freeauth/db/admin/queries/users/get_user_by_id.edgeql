SELECT
    User {
        name,
        username,
        email,
        mobile,
        org_type: { code, name },
        departments := (
            SELECT .directly_organizations {
                id,
                code,
                name,
                enterprise := assert_single(.ancestors {
                    id,
                    name
                } FILTER EXISTS [is Enterprise]),
                org_type := assert_single(.ancestors {
                    id,
                    name
                } FILTER EXISTS [is OrganizationType])
            }
        ),
        roles: {
            id,
            code,
            name,
            description,
            is_deleted,
            org_type: { code, name }
        },
        is_deleted,
        created_at,
        last_login_at
    }
FILTER .id = <uuid>$id;
