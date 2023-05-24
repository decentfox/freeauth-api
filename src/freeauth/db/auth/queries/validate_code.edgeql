with
    module auth,
    account := <str>$account,
    code_type := <CodeType>$code_type,
    verify_type := <VerifyType>$verify_type,
    code := <str>$code,
    max_attempts := <optional int64>$max_attempts,
    consumable_record := (
        select VerifyRecord
        filter .account = account
            and .code_type  = code_type
            and .verify_type = verify_type
            and .consumable
            and (.incorrect_attempts <= max_attempts) ?? true
    ),
    record := ( select consumable_record filter .code = code ),
    valid_record := (
        update record
        filter .expired_at > datetime_of_transaction()
        set {
            consumed_at := datetime_of_transaction()
        }
    ),
    incorrect_record := (
        update consumable_record
        filter exists max_attempts and not exists record
        set {
            incorrect_attempts := .incorrect_attempts + 1,
            expired_at := (
                datetime_of_transaction() if
                .incorrect_attempts = max_attempts - 1 else
                .expired_at
            )
        }
    ),
    code_attempts_exceeded := any(
        (incorrect_record.incorrect_attempts >= max_attempts) ?? false
    ),
    status_code := (
        AuditStatusCode.INVALID_CODE
        if not exists consumable_record
        else AuditStatusCode.CODE_ATTEMPTS_EXCEEDED
        if code_attempts_exceeded
        else AuditStatusCode.CODE_INCORRECT
        if not exists record
        else AuditStatusCode.CODE_EXPIRED
        if not exists valid_record
        else AuditStatusCode.OK
    )
select (
    status_code := status_code,
);
