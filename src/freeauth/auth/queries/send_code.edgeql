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
            AND EXISTS attempts_ttl
            AND EXISTS attempts_ttl
            AND .account = account
            AND .code_type  = code_type
            AND .verify_type = verify_type
            AND .created_at >= (
                datetime_of_transaction() -
                <cal::relative_duration>(
                    <str>attempts_ttl ++ ' minutes'
                )
            )
        )
    ),
FOR _ IN (
    SELECT true FILTER (
        true IF NOT EXISTS max_attempts ELSE
        count(sent_records) < max_attempts
    )
) UNION (
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
    }
);
