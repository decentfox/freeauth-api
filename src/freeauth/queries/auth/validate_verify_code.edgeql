WITH
    account := <str>$account,
    code_type := <auth::VerifyCodeType>$code_type,
    code := <str>$code,
    ttl := <str>$ttl,
    record := (
        SELECT auth::VerifyRecord
        FILTER .account = account
            AND .code_type  = code_type
            AND .code = code
    ),
    valid_record := (
        UPDATE record
        FILTER .created_at + <cal::relative_duration>ttl
                < datetime_of_transaction()
            AND NOT EXISTS .consumed_at
        SET {
            consumed_at := datetime_of_transaction()
        }
    )
SELECT (
    record := record,
    valid := valid_record = record
);
