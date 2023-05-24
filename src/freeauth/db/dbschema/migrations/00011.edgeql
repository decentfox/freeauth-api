CREATE MIGRATION m1bmljoubai5lk632o7ubp2pmfaltqbzust5aulzlwmbdwhngpmycq
    ONTO m1aandhgwtyob64wvbs2upheabwbwsbp3pbfpol3ycplq4ouvvb6qa
{
  CREATE ABSTRACT TYPE default::Organization EXTENDING default::TimeStamped {
      CREATE PROPERTY code -> std::str;
      CREATE PROPERTY code_upper := (std::str_upper(.code));
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  CREATE TYPE default::Department EXTENDING default::Organization {
      CREATE REQUIRED LINK parent -> default::Organization {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE PROPERTY description -> std::str;
  };
  ALTER TYPE default::Organization {
      CREATE MULTI LINK children := (.<parent[IS default::Department]);
  };
  CREATE TYPE default::Enterprise EXTENDING default::Organization {
      CREATE REQUIRED LINK org_type -> default::OrganizationType {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE CONSTRAINT std::exclusive ON ((.code_upper, .org_type));
      CREATE PROPERTY bank_account_number -> std::str;
      CREATE PROPERTY contact_address -> std::str;
      CREATE PROPERTY contact_phone_num -> std::str;
      CREATE PROPERTY issuing_bank -> std::str;
      CREATE PROPERTY tax_id -> std::str;
  };
  ALTER TYPE default::Department {
      CREATE REQUIRED LINK enterprise -> default::Enterprise;
      CREATE CONSTRAINT std::exclusive ON ((.code_upper, .enterprise));
  };
  ALTER TYPE default::OrganizationType {
      CREATE MULTI LINK enterprises := (.<org_type[IS default::Enterprise]);
      CREATE REQUIRED PROPERTY code -> std::str {
          SET REQUIRED USING (<std::str>.id);
      };
      CREATE REQUIRED PROPERTY code_upper := (std::str_upper(.code));
      CREATE CONSTRAINT std::exclusive ON (.code_upper);
  };
  UPDATE default::OrganizationType FILTER .is_protected = true SET {
      code := 'INNER'
  };
};
