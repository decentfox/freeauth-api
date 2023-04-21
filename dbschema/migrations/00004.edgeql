CREATE MIGRATION m1s2m5m5n3lfu2fef5xzxi2otaji72lytym6nynflas5sksmky4emq
    ONTO m1oo3sabmlzjuz3fseebv2qza2tnzee4oou4z5ufxrfj6ed25y37jq
{
  CREATE SCALAR TYPE auth::VerifyType EXTENDING enum<SignIn, SignUp>;
  ALTER TYPE auth::VerifyRecord {
      CREATE REQUIRED PROPERTY verify_type -> auth::VerifyType {
          SET readonly := true;
          SET REQUIRED USING (<auth::VerifyType>'SignIn');
      };
      CREATE CONSTRAINT std::exclusive ON ((.account, .code, .code_type, .verify_type));
      DROP INDEX ON ((.account, .code, .code_type));
      CREATE REQUIRED PROPERTY expired_at -> std::datetime {
          SET readonly := true;
          SET REQUIRED USING (std::datetime_of_transaction());
      };
  };
  ALTER SCALAR TYPE auth::VerifyCodeType RENAME TO auth::CodeType;
};
