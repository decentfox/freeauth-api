module default {
    global current_user_id -> uuid;
    global current_user := (
        select User filter .id = global current_user_id
    );

    type User extending TimeStamped {
        property username -> str {
            constraint exclusive;
        };
        property hashed_password -> str;
        property email -> str {
            constraint exclusive;
        };

        index on (.username);
        index on (.email);
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
