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
            AND .consumable
        ORDER BY .created_at DESC
        LIMIT 1
    ),
    valid_record := (
        UPDATE record
        FILTER .expired_at >= datetime_of_transaction()
        SET {
            consumed_at := datetime_of_transaction()
        }
    ),
    valid := EXISTS record AND EXISTS valid_record
SELECT (
    code_found := EXISTS record,
    code_valid := EXISTS valid_record
);
