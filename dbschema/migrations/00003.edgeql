CREATE MIGRATION m1oo3sabmlzjuz3fseebv2qza2tnzee4oou4z5ufxrfj6ed25y37jq
    ONTO m1rptqubhpcmn2ixpws5upufiiq3w7nwka5k3mch43v7yzthduuadq
{
  CREATE MODULE auth IF NOT EXISTS;
  CREATE ABSTRACT TYPE auth::Identity EXTENDING default::TimeStamped {
      CREATE REQUIRED LINK user -> default::User;
  };
  CREATE TYPE auth::EmailIdentity EXTENDING auth::Identity {
      CREATE REQUIRED PROPERTY email -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  CREATE TYPE auth::SMSIdentity EXTENDING auth::Identity {
      CREATE REQUIRED PROPERTY mobile -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  CREATE SCALAR TYPE auth::VerifyCodeType EXTENDING enum<SMS, Email>;
  CREATE TYPE auth::VerifyRecord EXTENDING default::TimeStamped {
      CREATE REQUIRED PROPERTY account -> std::str {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY code -> std::str {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY code_type -> auth::VerifyCodeType {
          SET readonly := true;
      };
      CREATE INDEX ON ((.account, .code, .code_type));
      CREATE PROPERTY consumed_at -> std::datetime;
  };
  DROP TYPE default::EmailAuth;
};
