WITH
    account := <str>$account,
    code_type := <auth::CodeType>$code_type,
    verify_type := <auth::VerifyType>$verify_type,
    code := <str>$code,
    record := (
        SELECT auth::VerifyRecord
        FILTER .account = account
            AND .code_type  = code_type
            AND .verify_type = verify_type
            AND .code = code
    ),
    valid_record := (
        UPDATE record
        FILTER .expired_at < datetime_of_transaction()
            AND NOT EXISTS .consumed_at
        SET {
            consumed_at := datetime_of_transaction()
        }
    )
SELECT (
    record
) {
    created_at,
    account,
    code,
    code_type,
    verify_type,
    expired_at,
    valid := EXISTS record AND valid_record = record
};
