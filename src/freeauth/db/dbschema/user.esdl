module default {
    global current_user_id -> uuid;
    global current_user := (
        select User filter .id = global current_user_id
    );

    type User extending TimeStamped, SoftDeletable {
        property name -> str;
        property username -> str {
            constraint exclusive;
        };
        property hashed_password -> str;
        property email -> str {
            constraint exclusive;
        };
        property mobile -> str {
            constraint exclusive;
        };
        property last_login_at -> datetime;

        multi link directly_organizations -> Organization {
            on target delete allow;
        };
        multi link organizations := (
            .directly_organizations.<ancestors[is Organization]
        );
        multi link roles -> Role {
            on target delete allow;
        };
        link org_type -> OrganizationType {
            on target delete allow;
        };
        multi link permissions := .roles.permissions;

        index on (.username);
        index on (.email);
        index on (.mobile);
    }
}
