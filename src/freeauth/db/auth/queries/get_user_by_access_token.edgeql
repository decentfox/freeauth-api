with
    token := (
        select auth::Token
        filter
            .access_token = <str>$access_token
            and .is_revoked = false
    )
select token { access_token, user };
