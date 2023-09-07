with
    module freeauth,
    username := <optional str>$username,
    mobile := <optional str>$mobile,
    email := <optional str>$email,
    start_dt := datetime_of_statement() - cal::to_relative_duration(minutes := <optional int64>$interval),
    user := assert_single((
        select User
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
            and .created_at >= start_dt
        order by .created_at desc
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
                .created_at >= start_dt
            )
    )
select user {
    hashed_password,
    is_deleted,
    recent_failed_attempts := count(recent_failed_attempts)
};
