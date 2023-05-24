CREATE MIGRATION m1gdb7pc5d5ecwytpjgimgq3m5axq7jz3uwtsemnwk37ihkh2x5vvq
    ONTO m1fjzmzeffqkvaaltlomphzmfwmzm6ghtvg7bg23khvvdwezrv6x2q
{
  CREATE TYPE default::Permission EXTENDING default::TimeStamped, default::SoftDeletable {
      CREATE PROPERTY code -> std::str;
      CREATE PROPERTY code_upper := (std::str_upper(.code));
      CREATE CONSTRAINT std::exclusive ON (.code_upper);
      CREATE PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  ALTER TYPE default::Role {
      CREATE MULTI LINK permissions -> default::Permission {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE default::Permission {
      CREATE MULTI LINK roles := (.<permissions[IS default::Role]);
  };
};
