module auth {
    scalar type CodeType extending enum<SMS, Email>;
    scalar type VerifyType extending enum<SignIn, SignUp>;
    scalar type AuditEventType extending enum<SignIn, SignOut, SignUp>;

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

    type AuditLog extending default::TimeStamped {
        required link user -> default::User;
        required property client_ip -> str {
            readonly := true;
        }
        required property event_type -> AuditEventType {
            readonly := true;
        };
        required property status_code -> int16 {
            readonly := true;
        };
        property is_succeed := .status_code = 200;
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
