module auth {
    scalar type VerifyCodeType extending enum<SMS, Email>;

    type VerifyRecord extending default::TimeStamped {
        required property account -> str {
            readonly := true;
        };
        required property code -> str {
            readonly := true;
        };
        required property code_type -> VerifyCodeType {
            readonly := true;
        };
        property consumed_at -> datetime;

        constraint exclusive on ((.account, .code, .code_type));
    }

    abstract type Identity extending default::TimeStamped {
        required link user -> default::User;
    }

    type SMSIdentity extending Identity {
        required property mobile -> str {
            constraint exclusive;
        }
    }

    type EmailIdentity extending Identity {
        required property email -> str {
            constraint exclusive;
        }
    }
}
