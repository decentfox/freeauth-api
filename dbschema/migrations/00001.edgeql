CREATE MIGRATION m1cqvbfpbxm57442wylruznsbcl25fnfze7h7wcxw35muotbqwnffa
    ONTO initial
{
  CREATE FUTURE nonrecursive_access_policies;
  CREATE GLOBAL default::current_user_id -> std::uuid;
  CREATE ABSTRACT TYPE default::TimeStamped {
      CREATE REQUIRED PROPERTY created_at -> std::datetime {
          SET default := (std::datetime_of_transaction());
          SET readonly := true;
      };
      CREATE INDEX ON (.created_at);
  };
  CREATE TYPE default::User EXTENDING default::TimeStamped {
      CREATE PROPERTY email -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY hashed_password -> std::str;
      CREATE PROPERTY username -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON (.username);
      CREATE INDEX ON (.email);
  };
  CREATE GLOBAL default::current_user := (SELECT
      default::User
  FILTER
      (.id = GLOBAL default::current_user_id)
  );
  CREATE TYPE default::EmailAuth EXTENDING default::TimeStamped {
      CREATE REQUIRED PROPERTY code -> std::str {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY email -> std::str {
          SET readonly := true;
      };
      CREATE INDEX ON ((.email, .code));
      CREATE PROPERTY token -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON (.token);
      CREATE REQUIRED LINK user -> default::User;
  };
};
