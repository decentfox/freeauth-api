WITH
    account := <str>$account,
    code_type := <auth::CodeType>$code_type,
    verify_type := <auth::VerifyType>$verify_type,
    code := <str>$code,
    ttl := <int16>$ttl,
    max_attempts := <optional int64>$max_attempts,
    attempts_ttl := <optional int16>$attempts_ttl,
    sent_records := (
        SELECT auth::VerifyRecord
        FILTER (
            EXISTS max_attempts
            AND .account = account
            AND .code_type  = code_type
            AND .verify_type = verify_type
            AND .created_at >= (
                datetime_of_transaction() -
                cal::to_relative_duration(minutes := attempts_ttl)
            )
        )
    ),
FOR _ IN (
    SELECT true FILTER
        (count(sent_records) < max_attempts) ?? true
) UNION (
    SELECT (
        INSERT auth::VerifyRecord {
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
