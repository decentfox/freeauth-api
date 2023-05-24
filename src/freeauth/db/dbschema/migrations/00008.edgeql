CREATE MIGRATION m1aotx76nsod5ol5ijpfbdt3rjokip2ph5anfji2vseprsvfsfaw7a
    ONTO m1ueu3ll6in5uxa7cdd3z7wsxndrdn2kunsmeucqybkhk4wcjfojvq
{
  CREATE TYPE default::LoginSetting {
      CREATE REQUIRED PROPERTY key -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON (.key);
      CREATE REQUIRED PROPERTY value -> std::str;
  };
};
