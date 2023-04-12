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

        index on (.username);
        index on (.email);
        index on (.mobile);
    }

    type EmailAuth extending TimeStamped {
        required property email -> str {
            readonly := true;
        };
        required property code -> str {
            readonly := true;
        };
        property token -> str {
            constraint exclusive;
        };

        required link user -> User;

        index on (.token);
        index on ((.email, .code));
    }
}
