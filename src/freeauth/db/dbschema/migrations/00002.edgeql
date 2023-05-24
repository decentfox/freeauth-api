CREATE MIGRATION m1rptqubhpcmn2ixpws5upufiiq3w7nwka5k3mch43v7yzthduuadq
    ONTO m1cqvbfpbxm57442wylruznsbcl25fnfze7h7wcxw35muotbqwnffa
{
  CREATE ABSTRACT TYPE default::SoftDeletable {
      CREATE PROPERTY deleted_at -> std::datetime;
      CREATE PROPERTY is_deleted := (EXISTS (.deleted_at));
      CREATE INDEX ON (.is_deleted);
  };
  ALTER TYPE default::User EXTENDING default::SoftDeletable LAST;
  ALTER TYPE default::User {
      CREATE PROPERTY last_login_at -> std::datetime;
  };
  ALTER TYPE default::User {
      CREATE PROPERTY mobile -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  ALTER TYPE default::User {
      CREATE PROPERTY name -> std::str;
  };
  ALTER TYPE default::User {
      CREATE INDEX ON (.mobile);
  };
};
