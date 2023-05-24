CREATE MIGRATION m1ueu3ll6in5uxa7cdd3z7wsxndrdn2kunsmeucqybkhk4wcjfojvq
    ONTO m1e53oun6isassd7qc2s7aeolz4lunopwhufmfq47r7ti7plympxnq
{
  CREATE SCALAR TYPE auth::AuditEventType EXTENDING enum<SignIn, SignOut, SignUp>;
  CREATE TYPE auth::AuditLog EXTENDING default::TimeStamped {
      CREATE REQUIRED PROPERTY status_code -> std::int16 {
          SET readonly := true;
      };
      CREATE PROPERTY is_succeed := ((.status_code = 200));
      CREATE INDEX ON (.is_succeed);
      CREATE REQUIRED PROPERTY event_type -> auth::AuditEventType {
          SET readonly := true;
      };
      CREATE INDEX ON (.event_type);
      CREATE REQUIRED LINK user -> default::User;
      CREATE PROPERTY browser -> std::str {
          SET readonly := true;
      };
      CREATE REQUIRED PROPERTY client_ip -> std::str {
          SET readonly := true;
      };
      CREATE PROPERTY device -> std::str {
          SET readonly := true;
      };
      CREATE PROPERTY os -> std::str {
          SET readonly := true;
      };
      CREATE PROPERTY raw_ua -> std::str {
          SET readonly := true;
      };
  };
};
