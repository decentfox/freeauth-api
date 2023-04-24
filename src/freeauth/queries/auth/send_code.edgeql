WITH
    account := <str>$account,
    code_type := <auth::CodeType>$code_type,
    verify_type := <auth::VerifyType>$verify_type,
    code := <str>$code,
    ttl := <int16>$ttl
SELECT (
    INSERT auth::VerifyRecord {
        account := account,
        code_type := code_type,
        verify_type := verify_type,
        code := code,
        expired_at := (
            datetime_of_transaction() +
            <cal::relative_duration>(<str>ttl ++ ' seconds')
        )
    }
) {
    created_at,
    account,
    code_type,
    verify_type,
    expired_at,
    ttl := ttl
};
