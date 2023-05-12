module auth {
    scalar type CodeType extending enum<SMS, Email>;
    scalar type VerifyType extending enum<SignIn, SignUp>;
    scalar type AuditEventType extending enum<SignIn, SignOut, SignUp>;
    scalar type AuditStatusCode extending
    enum<
        OK,
        ACCOUNT_ALREADY_EXISTS,
        ACCOUNT_NOT_EXISTS,
        ACCOUNT_DISABLED,
        INVALID_PASSWORD,
        PASSWORD_ATTEMPTS_EXCEEDED,
        INVALID_CODE,
        CODE_ATTEMPTS_EXCEEDED,
        CODE_EXPIRED,
    >;

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
        required property expired_at -> datetime;
        property consumed_at -> datetime;
        required property consumable := not exists .consumed_at;
        required property incorrect_attempts -> int64 {
            default := 0
        };

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

    type AuditLog extending default::TimeStamped {
        link user -> default::User;
        required property client_ip -> str {
            readonly := true;
        }
        required property event_type -> AuditEventType {
            readonly := true;
        };
        required property status_code -> AuditStatusCode {
            readonly := true;
        };
        required property is_succeed -> bool {
            default := true;
        };
        property raw_ua -> str {
            readonly := true;
        };
        property os -> str {
            readonly := true;
        };
        property device -> str {
            readonly := true;
        };
        property browser -> str {
            readonly := true;
        };

        index on (.event_type);
        index on (.is_succeed);
    }
}
