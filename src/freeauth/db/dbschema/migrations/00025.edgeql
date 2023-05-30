CREATE MIGRATION m17uiwcmjgs2uxxgcfi3qb2ddqijuoencbr74xc42cqiq7esqnnr6q
    ONTO m1pwk6wff5r2xbxtjeesr6x76xw6wksmmvmeqlt6rkczev3z4ch7wq
{
  CREATE GLOBAL default::current_app_id -> std::uuid;
  ALTER TYPE default::Application {
      ALTER PROPERTY secret_key {
          RENAME TO hashed_secret;
      };
  };
  CREATE GLOBAL default::current_app := (SELECT
      default::Application
  FILTER
      (.id = GLOBAL default::current_app_id)
  );
  ALTER TYPE default::Permission {
      DROP CONSTRAINT std::exclusive ON (.code_upper);
  };
  ALTER TYPE default::Permission {
      CREATE CONSTRAINT std::exclusive ON ((.code_upper, .application));
  };
  ALTER TYPE default::User {
      CREATE MULTI LINK permissions := (.roles.permissions);
  };
};
