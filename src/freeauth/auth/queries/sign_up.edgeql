WITH
    name := <optional str>$name,
    username := <str>$username,
    email := <optional str>$email,
    mobile := <optional str>$mobile,
    hashed_password := <str>$hashed_password,
    client_info := (
        <tuple<client_ip: str, user_agent: json>><json>$client_info
    ),
    user := (
        INSERT User {
            name := name,
            username := username,
            email := email,
            mobile := mobile,
            hashed_password := hashed_password
        }
    ),
    audit_log := (
        INSERT auth::AuditLog {
            client_ip := <str>client_info.client_ip,
            event_type := <auth::AuditEventType>'SignUp',
            status_code := <int16>200,
            raw_ua := <str>client_info.user_agent['raw_ua'],
            os := <str>client_info.user_agent['os'],
            device := <str>client_info.user_agent['device'],
            browser := <str>client_info.user_agent['browser'],
            user := user
        }
    )
SELECT user {
    name,
    username,
    email,
    mobile,
    is_deleted,
    created_at,
    last_login_at
};
