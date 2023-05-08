CREATE MIGRATION m1e5hi6ymifyqavmoos576n7n7obeqg2m5qe2dqcf6h2swjg5qo2ca
    ONTO m1u4ogrpaes2irqcrqrvjhawbhoehnabnjviqcyzumxknee6lhx4la
{
  ALTER TYPE default::OrganizationType {
      DROP CONSTRAINT std::exclusive ON (.code_upper);
  };
  ALTER TYPE default::OrganizationType {
      DROP PROPERTY code_upper;
      EXTENDING default::Organization BEFORE default::SoftDeletable;
  };
  ALTER TYPE default::OrganizationType {
      ALTER PROPERTY code {
          RESET OPTIONALITY;
          DROP OWNED;
          RESET TYPE;
      };
  };
  ALTER TYPE default::OrganizationType {
      CREATE CONSTRAINT std::exclusive ON (.code_upper);
  };
  ALTER TYPE default::OrganizationType {
      ALTER PROPERTY name {
          RESET OPTIONALITY;
          DROP OWNED;
          RESET TYPE;
      };
  };
  CREATE TYPE default::Role EXTENDING default::TimeStamped, default::SoftDeletable {
      CREATE PROPERTY code -> std::str;
      CREATE PROPERTY code_upper := (std::str_upper(.code));
      CREATE CONSTRAINT std::exclusive ON (.code_upper);
      CREATE MULTI LINK organizations -> default::Organization {
          ON TARGET DELETE ALLOW;
      };
      CREATE PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY name -> std::str;
  };
};
