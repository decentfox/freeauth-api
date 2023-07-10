with
    module freeauth,
    client_info := (
        <tuple<client_ip: str, user_agent: json>><json>$client_info
    ),
    user := (
        update User
        filter .id = <uuid>$id
        set { last_login_at := datetime_of_transaction() }
    ),
    token := (
        insert Token {
            access_token := <str>$access_token,
            user := user
        }
    ),
    audit_log := (
        insert AuditLog {
            client_ip := client_info.client_ip,
            event_type := AuditEventType.SignIn,
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
