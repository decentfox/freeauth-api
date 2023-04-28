WITH
    client_info := (
        <tuple<client_ip: str, user_agent: json>><json>$client_info
    ),
    user := (
        UPDATE User
        FILTER .id = <uuid>$id
        SET { last_login_at := datetime_of_transaction() }
    ),
    token := (
        INSERT auth::Token {
            access_token := <str>$access_token,
            user := user
        }
    ),
    audit_log := (
        INSERT auth::AuditLog {
            client_ip := <str>client_info.client_ip,
            event_type := <auth::AuditEventType>'SignIn',
            status_code := <int16>200,
            raw_ua := <str>client_info.user_agent['raw_ua'],
            os := <str>client_info.user_agent['os'],
            device := <str>client_info.user_agent['device'],
            browser := <str>client_info.user_agent['browser'],
            user := user
        }
    )
SELECT user {
    id, name, username, email, mobile,
    is_deleted, created_at, last_login_at
};
