with
    module auth,
    client_info := (
        <tuple<client_ip: str, user_agent: json>><json>$client_info
    ),
    user := (
        update default::User
        filter
            .id = <uuid>$id and not .is_deleted
        set {
            hashed_password := <str>$hashed_password,
            reset_pwd_on_next_login := false,
        }
    ),
    audit_log := (
        insert AuditLog {
            client_ip := client_info.client_ip,
            event_type := AuditEventType.ResetPwd,
            status_code := AuditStatusCode.OK,
            raw_ua := <str>client_info.user_agent['raw_ua'],
            os := <str>client_info.user_agent['os'],
            device := <str>client_info.user_agent['device'],
            browser := <str>client_info.user_agent['browser'],
            user := user
        }
    )
select user { id, is_deleted };
