CREATE MIGRATION m1tbegoksyubjz3i64c5grkdxzzrudz4664qpr72pg7zcxj223k66q
    ONTO initial
{
  CREATE MODULE freeauth IF NOT EXISTS;
  CREATE FUTURE nonrecursive_access_policies;
  CREATE GLOBAL freeauth::current_app_id -> std::uuid;
  CREATE ABSTRACT TYPE freeauth::TimeStamped {
      CREATE REQUIRED PROPERTY created_at -> std::datetime {
          SET default := (std::datetime_of_transaction());
          SET readonly := true;
      };
      CREATE INDEX ON (.created_at);
  };
  CREATE ABSTRACT TYPE freeauth::SoftDeletable {
      CREATE PROPERTY deleted_at -> std::datetime;
      CREATE PROPERTY is_deleted := (EXISTS (.deleted_at));
      CREATE INDEX ON (.is_deleted);
  };
  CREATE TYPE freeauth::Application EXTENDING freeauth::TimeStamped, freeauth::SoftDeletable {
      CREATE PROPERTY description -> std::str;
      CREATE PROPERTY hashed_secret -> std::str;
      CREATE REQUIRED PROPERTY is_protected -> std::bool {
          SET default := false;
      };
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  CREATE GLOBAL freeauth::current_app := (SELECT
      freeauth::Application
  FILTER
      (.id = GLOBAL freeauth::current_app_id)
  );
  CREATE GLOBAL freeauth::current_user_id -> std::uuid;
  CREATE TYPE freeauth::User EXTENDING freeauth::TimeStamped, freeauth::SoftDeletable {
      CREATE PROPERTY email -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY hashed_password -> std::str;
      CREATE PROPERTY last_login_at -> std::datetime;
      CREATE PROPERTY mobile -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY name -> std::str;
      CREATE PROPERTY reset_pwd_on_next_login -> std::bool {
          SET default := false;
      };
      CREATE PROPERTY username -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON (.mobile);
      CREATE INDEX ON (.username);
      CREATE INDEX ON (.email);
  };
  CREATE GLOBAL freeauth::current_user := (SELECT
      freeauth::User
  FILTER
      (.id = GLOBAL freeauth::current_user_id)
  );
  CREATE ABSTRACT TYPE freeauth::Tag EXTENDING freeauth::TimeStamped {
      CREATE REQUIRED PROPERTY name -> std::str;
      CREATE PROPERTY rank -> std::int16;
  };
  CREATE TYPE freeauth::PermissionTag EXTENDING freeauth::Tag {
      CREATE CONSTRAINT std::exclusive ON (.name);
  };
  CREATE TYPE freeauth::Permission EXTENDING freeauth::TimeStamped, freeauth::SoftDeletable {
      CREATE REQUIRED LINK application -> freeauth::Application {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE REQUIRED PROPERTY code -> std::str;
      CREATE PROPERTY code_upper := (std::str_upper(.code));
      CREATE CONSTRAINT std::exclusive ON ((.code_upper, .application));
      CREATE ACCESS POLICY full_access
          ALLOW ALL ;
      CREATE ACCESS POLICY readonly_wildcard_perm
          DENY UPDATE, DELETE USING ((.code = '*'));
      CREATE MULTI LINK tags -> freeauth::PermissionTag {
          ON TARGET DELETE ALLOW;
      };
      CREATE PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  ALTER TYPE freeauth::Application {
      CREATE MULTI LINK permissions := (.<application[IS freeauth::Permission]);
  };
  CREATE SCALAR TYPE freeauth::AuditEventType EXTENDING enum<SignIn, SignOut, SignUp, ResetPwd>;
  CREATE SCALAR TYPE freeauth::AuditStatusCode EXTENDING enum<OK, ACCOUNT_ALREADY_EXISTS, ACCOUNT_NOT_EXISTS, ACCOUNT_DISABLED, INVALID_PASSWORD, PASSWORD_ATTEMPTS_EXCEEDED, INVALID_CODE, CODE_INCORRECT, CODE_ATTEMPTS_EXCEEDED, CODE_EXPIRED>;
  CREATE TYPE freeauth::AuditLog EXTENDING freeauth::TimeStamped {
      CREATE REQUIRED PROPERTY event_type -> freeauth::AuditEventType {
          SET readonly := true;
      };
      CREATE INDEX ON (.event_type);
      CREATE REQUIRED LINK user -> freeauth::User {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE PROPERTY browser -> std::str {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY client_ip -> std::str {
          SET readonly := true;
      };
      CREATE PROPERTY device -> std::str {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY status_code -> freeauth::AuditStatusCode {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY is_succeed := ((.status_code = freeauth::AuditStatusCode.OK));
      CREATE PROPERTY os -> std::str {
          SET readonly := true;
      };
      CREATE PROPERTY raw_ua -> std::str {
          SET readonly := true;
      };
  };
  CREATE ABSTRACT TYPE freeauth::Organization EXTENDING freeauth::TimeStamped {
      CREATE MULTI LINK ancestors -> freeauth::Organization {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE MULTI LINK children := (.<ancestors[IS freeauth::Organization]);
      CREATE PROPERTY code -> std::str;
      CREATE PROPERTY code_upper := (std::str_upper(.code));
      CREATE REQUIRED PROPERTY hierarchy := (std::count(.ancestors));
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  CREATE TYPE freeauth::Department EXTENDING freeauth::Organization {
      CREATE REQUIRED LINK parent -> freeauth::Organization {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE PROPERTY description -> std::str;
  };
  ALTER TYPE freeauth::Organization {
      CREATE MULTI LINK directly_children := (.<parent[IS freeauth::Department]);
  };
  ALTER TYPE freeauth::User {
      CREATE MULTI LINK directly_organizations -> freeauth::Organization {
          ON TARGET DELETE ALLOW;
      };
      CREATE MULTI LINK organizations := (.directly_organizations.<ancestors[IS freeauth::Organization]);
  };
  ALTER TYPE freeauth::Organization {
      CREATE MULTI LINK directly_users := (.<directly_organizations[IS freeauth::User]);
      CREATE MULTI LINK users := (SELECT
          DISTINCT (((SELECT
              .directly_users
          ) UNION (SELECT
              .<ancestors[IS freeauth::Organization].directly_users
          )))
      );
  };
  CREATE TYPE freeauth::Enterprise EXTENDING freeauth::Organization {
      CREATE PROPERTY bank_account_number -> std::str;
      CREATE PROPERTY contact_address -> std::str;
      CREATE PROPERTY contact_phone_num -> std::str;
      CREATE PROPERTY issuing_bank -> std::str;
      CREATE PROPERTY tax_id -> std::str;
  };
  ALTER TYPE freeauth::Department {
      CREATE REQUIRED LINK enterprise -> freeauth::Enterprise {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE CONSTRAINT std::exclusive ON ((.code_upper, .enterprise));
  };
  CREATE TYPE freeauth::OrganizationType EXTENDING freeauth::Organization, freeauth::SoftDeletable {
      CREATE CONSTRAINT std::exclusive ON (.code_upper);
      CREATE PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY is_protected -> std::bool {
          SET default := false;
      };
  };
  ALTER TYPE freeauth::Enterprise {
      CREATE REQUIRED LINK org_type -> freeauth::OrganizationType {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE CONSTRAINT std::exclusive ON ((.code_upper, .org_type));
  };
  ALTER TYPE freeauth::OrganizationType {
      CREATE MULTI LINK enterprises := (.<org_type[IS freeauth::Enterprise]);
  };
  CREATE TYPE freeauth::LoginSetting {
      CREATE REQUIRED PROPERTY key -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON (.key);
      CREATE REQUIRED PROPERTY value -> std::str;
  };
  CREATE TYPE freeauth::Role EXTENDING freeauth::TimeStamped, freeauth::SoftDeletable {
      CREATE LINK org_type -> freeauth::OrganizationType {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE MULTI LINK permissions -> freeauth::Permission {
          ON TARGET DELETE ALLOW;
      };
      CREATE PROPERTY code -> std::str;
      CREATE PROPERTY code_upper := (std::str_upper(.code));
      CREATE CONSTRAINT std::exclusive ON (.code_upper);
      CREATE PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  ALTER TYPE freeauth::OrganizationType {
      CREATE MULTI LINK roles := (.<org_type[IS freeauth::Role]);
  };
  ALTER TYPE freeauth::User {
      CREATE LINK org_type -> freeauth::OrganizationType {
          ON TARGET DELETE ALLOW;
      };
      CREATE MULTI LINK roles -> freeauth::Role {
          ON TARGET DELETE ALLOW;
      };
      CREATE MULTI LINK permissions := (.roles.permissions);
  };
  ALTER TYPE freeauth::Permission {
      CREATE MULTI LINK roles := (.<permissions[IS freeauth::Role]);
  };
  ALTER TYPE freeauth::Role {
      CREATE MULTI LINK users := (.<roles[IS freeauth::User]);
  };
  CREATE TYPE freeauth::Token EXTENDING freeauth::TimeStamped {
      CREATE REQUIRED LINK user -> freeauth::User {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE REQUIRED PROPERTY access_token -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY revoked_at -> std::datetime;
      CREATE PROPERTY is_revoked := (EXISTS (.revoked_at));
  };
  CREATE SCALAR TYPE freeauth::CodeType EXTENDING enum<SMS, Email>;
  CREATE SCALAR TYPE freeauth::VerifyType EXTENDING enum<SignIn, SignUp>;
  CREATE TYPE freeauth::VerifyRecord EXTENDING freeauth::TimeStamped {
      CREATE REQUIRED PROPERTY account -> std::str {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY code_type -> freeauth::CodeType {
          SET readonly := true;
      };
      CREATE PROPERTY consumed_at -> std::datetime;
      CREATE REQUIRED PROPERTY consumable := (NOT (EXISTS (.consumed_at)));
      CREATE REQUIRED PROPERTY verify_type -> freeauth::VerifyType {
          SET readonly := true;
      };
      CREATE INDEX ON ((.account, .code_type, .verify_type, .consumable));
      CREATE REQUIRED PROPERTY code -> std::str {
          SET readonly := true;
      };
      CREATE INDEX ON (.code);
      CREATE REQUIRED PROPERTY expired_at -> std::datetime;
      CREATE REQUIRED PROPERTY incorrect_attempts -> std::int64 {
          SET default := 0;
      };
  };
};
