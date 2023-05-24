with
    token := (
        select auth::Token
        filter
            .access_token = <str>$access_token
            and .is_revoked = false
    )
select
    User {
        name,
        username,
        email,
        mobile,
        org_type: { code, name },
        departments := (
            select .directly_organizations { code, name }
        ),
        roles: { code, name },
        is_deleted,
        created_at,
        last_login_at
    }
filter User = token.user
