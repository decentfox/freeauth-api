CREATE MIGRATION m1ufulacs2qjkeiamqhos6uiduu3oasyfvw672iamuyx3i22gen2ta
    ONTO m1fhh6hqsmblbhx6f5ymfuirfafd77p5h5qn2r3655t3ama6otydlq
{
  ALTER TYPE auth::AuditLog {
      ALTER LINK user {
          RESET OPTIONALITY;
      };
  };
  ALTER TYPE auth::AuditLog {
      DROP INDEX ON (.is_succeed);
  };
  ALTER TYPE auth::AuditLog {
      DROP PROPERTY is_succeed;
  };
  CREATE SCALAR TYPE auth::AuditStatusCode EXTENDING enum<OK, ACCOUNT_ALREADY_EXISTS, ACCOUNT_NOT_EXISTS, ACCOUNT_DISABLED, INVALID_PASSWORD, PASSWORD_ATTEMPTS_EXCEEDED, INVALID_CODE, CODE_ATTEMPTS_EXCEEDED, CODE_EXPIRED>;
  ALTER TYPE auth::AuditLog {
      ALTER PROPERTY status_code {
          SET TYPE auth::AuditStatusCode USING (auth::AuditStatusCode.OK);
      };
  };
  ALTER TYPE auth::AuditLog {
      CREATE REQUIRED PROPERTY is_succeed -> std::bool {
          SET default := true;
      };
      CREATE INDEX ON (.is_succeed);
  };

};
