CREATE MIGRATION m1e53oun6isassd7qc2s7aeolz4lunopwhufmfq47r7ti7plympxnq
    ONTO m1dkkpaxgqcxdrgvns3jyabvqnhyfm3fq4uransv5kgbpo7eai74ia
{
  ALTER TYPE auth::Identity {
      DROP LINK user;
  };
  DROP TYPE auth::EmailIdentity;
  DROP TYPE auth::SMSIdentity;
  DROP TYPE auth::Identity;
  CREATE TYPE auth::Token EXTENDING default::TimeStamped {
      CREATE REQUIRED LINK user -> default::User;
      CREATE REQUIRED PROPERTY access_token -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY revoked_at -> std::datetime;
      CREATE PROPERTY is_revoked := (EXISTS (.revoked_at));
  };
};
