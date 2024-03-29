with
    module freeauth,
    name := <optional str>$name,
    username := <str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    hashed_password := <str>$hashed_password,
    reset_pwd_on_next_login := <bool>$reset_pwd_on_next_login,
    client_info := (
        <tuple<client_ip: str, user_agent: json>><json>$client_info
    ),
    user := (
        insert User {
            name := name,
            username := username,
            email := email,
            mobile := mobile,
            hashed_password := hashed_password,
            reset_pwd_on_next_login := reset_pwd_on_next_login
        }
    ),
    audit_log := (
        insert AuditLog {
            client_ip := client_info.client_ip,
            event_type := AuditEventType.SignUp,
            status_code := AuditStatusCode.OK,
            raw_ua := <str>client_info.user_agent['raw_ua'],
            os := <str>client_info.user_agent['os'],
            device := <str>client_info.user_agent['device'],
            browser := <str>client_info.user_agent['browser'],
            user := user
        }
    )
select user {
    name,
    username,
    email,
    mobile,
    org_type: { code, name },
    departments := (
        select .directly_organizations { code, name }
    ),
    roles: { code, name },
    is_deleted,
    created_at,
    last_login_at
};
