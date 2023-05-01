CREATE MIGRATION m1aandhgwtyob64wvbs2upheabwbwsbp3pbfpol3ycplq4ouvvb6qa
    ONTO m1v7kijuudrt2n6kttcv5ohwnmu4wxgr7qmlffx3pi27cjuwql3uma
{
  ALTER TYPE auth::VerifyRecord {
      ALTER PROPERTY expired_at {
          RESET readonly;
      };
  };
  ALTER TYPE auth::VerifyRecord {
      CREATE REQUIRED PROPERTY incorrect_attempts -> std::int64 {
          SET default := 0;
      };
  };
};
