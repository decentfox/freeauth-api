with
    module freeauth,
    user := (
        select User filter .id = <uuid>$user_id
    ),
    client_info := (
        <tuple<client_ip: str, user_agent: json>><json>$client_info
    ),
    status_code := <AuditStatusCode>$status_code
select (
    insert AuditLog {
        client_ip := <str>client_info.client_ip,
        event_type := <AuditEventType>$event_type,
        status_code := status_code,
        raw_ua := <str>client_info.user_agent['raw_ua'],
        os := <str>client_info.user_agent['os'],
        device := <str>client_info.user_agent['device'],
        browser := <str>client_info.user_agent['browser'],
        user := user
    }
) {
    client_ip,
    os,
    device,
    browser,
    status_code,
    is_succeed,
    event_type,
    created_at,
    user: {
        username,
        mobile,
        email
    }
};
