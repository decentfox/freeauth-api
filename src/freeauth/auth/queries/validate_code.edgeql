WITH
    account := <str>$account,
    code_type := <auth::CodeType>$code_type,
    verify_type := <auth::VerifyType>$verify_type,
    code := <str>$code,
    max_attempts := <optional int64>$max_attempts,
    consumable_record := (
        SELECT auth::VerifyRecord
        FILTER .account = account
            AND .code_type  = code_type
            AND .verify_type = verify_type
            AND .consumable
            AND (
                true IF NOT EXISTS max_attempts ELSE
                .incorrect_attempts <= max_attempts
            )
        ORDER BY .created_at DESC
        LIMIT 1
    ),
    record := (SELECT consumable_record FILTER .code = code),
    valid_record := (
        UPDATE record
        FILTER .expired_at > datetime_of_transaction()
        SET {
            consumed_at := datetime_of_transaction()
        }
    ),
    incorrect_record := (
        UPDATE consumable_record
        FILTER EXISTS max_attempts AND NOT EXISTS record
        SET {
            incorrect_attempts := .incorrect_attempts + 1,
            expired_at := (
                datetime_of_transaction() IF
                .incorrect_attempts = max_attempts - 1 ELSE
                .expired_at
            )
        }
    )
SELECT (
    code_required := NOT EXISTS consumable_record,
    code_found := EXISTS record,
    code_valid := EXISTS valid_record,
    incorrect_attempts := (
        incorrect_record.incorrect_attempts ??
        consumable_record.incorrect_attempts ?? 0
    )
);
