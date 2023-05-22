update auth::Token
filter
    .access_token = <str>$access_token
    and .is_revoked = false
set {
    revoked_at := datetime_of_transaction()
};
