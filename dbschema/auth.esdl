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

        constraint exclusive on ((.account, .code, .code_type, .verify_type));
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
