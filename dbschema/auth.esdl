module auth {
    scalar type CodeType extending enum<SMS, Email>;
    scalar type VerifyType extending enum<SignIn, SignUp>;

    type VerifyRecord extending default::TimeStamped {
        required property account -> str {
            readonly := true;
        };
        required property code -> str {
            readonly := true;
        };
        required property code_type -> CodeType {
            readonly := true;
        };
        required property verify_type -> VerifyType {
            readonly := true;
        };
        required property expired_at -> datetime {
            readonly := true;
        }
        property consumed_at -> datetime;
        required property consumable := not exists .consumed_at;

        index on (.code);
        index on ((.account, .code_type, .verify_type, .consumable));
    }

    type Token extending default::TimeStamped {
        required link user -> default::User;
        required property access_token -> str {
            constraint exclusive;
        }
        property revoked_at -> datetime;
        property is_revoked := exists .revoked_at;
    }
}
