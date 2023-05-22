with
    module auth,
    username := <optional str>$username,
    mobile := <optional str>$mobile,
    email := <optional str>$email,
    interval := <optional int64>$interval,
    user := assert_single((
        select default::User
        filter
            (exists username and .username ?= username) or
            (exists mobile and .mobile ?= mobile) or
            (exists email and .email ?= email)
    )),
    recent_success_attempt := (
        select AuditLog
        filter
            .user = user
            and .event_type = AuditEventType.SignIn
            and .status_code = AuditStatusCode.OK
            and .created_at >= (
                datetime_of_statement() -
                cal::to_relative_duration(minutes := interval)
            )
        limit 1
    ),
    recent_failed_attempts := (
        select AuditLog
        filter
            .user = user
            and .event_type = AuditEventType.SignIn
            and .status_code = AuditStatusCode.INVALID_PASSWORD
            and (
                .created_at >= recent_success_attempt.created_at
                if exists recent_success_attempt else
                .created_at >= (
                    datetime_of_statement() -
                    cal::to_relative_duration(minutes := interval)
                )
            )
    )
select user {
    hashed_password,
    is_deleted,
    recent_failed_attempts := count(recent_failed_attempts)
};
