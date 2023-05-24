with
    account := <str>$account,
    code_type := <auth::CodeType>$code_type,
    verify_type := <auth::VerifyType>$verify_type,
    code := <str>$code,
    ttl := <int16>$ttl,
    max_attempts := <optional int64>$max_attempts,
    attempts_ttl := <optional int16>$attempts_ttl,
    sent_records := (
        select auth::VerifyRecord
        filter (
            exists max_attempts
            and .account = account
            and .code_type  = code_type
            and .verify_type = verify_type
            and .created_at >= (
                datetime_of_transaction() -
                cal::to_relative_duration(minutes := attempts_ttl)
            )
        )
    ),
for _ in (
    select true filter
        (count(sent_records) < max_attempts) ?? true
) union (
    select (
        insert auth::VerifyRecord {
            account := account,
            code_type := code_type,
            verify_type := verify_type,
            code := code,
            expired_at := (
                datetime_of_transaction() +
                cal::to_relative_duration(seconds := ttl)
            )
        }
    ) {
        created_at,
        account,
        code_type,
        verify_type,
        expired_at,
        ttl := ttl
    }
);
