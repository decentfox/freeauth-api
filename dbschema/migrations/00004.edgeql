CREATE MIGRATION m1web3yqimll7mohct5mzcfpfqz2c6h2g34jbokisj6iipjru4v24q
    ONTO m1oo3sabmlzjuz3fseebv2qza2tnzee4oou4z5ufxrfj6ed25y37jq
{
  CREATE SCALAR TYPE auth::VerifyType EXTENDING enum<Login, Register>;
  ALTER TYPE auth::VerifyRecord {
      CREATE REQUIRED PROPERTY verify_type -> auth::VerifyType {
          SET readonly := true;
          SET REQUIRED USING (auth::VerifyType.Login);
      };
      CREATE CONSTRAINT std::exclusive ON ((.account, .code, .code_type, .verify_type));
      DROP INDEX ON ((.account, .code, .code_type));
      CREATE REQUIRED PROPERTY expired_at -> std::datetime {
          SET readonly := true;
          SET REQUIRED USING ((.created_at + <cal::relative_duration>(<std::str>300 ++ ' seconds')));
      };
  };
  ALTER SCALAR TYPE auth::VerifyCodeType RENAME TO auth::CodeType;
};
