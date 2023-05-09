CREATE MIGRATION m1xv4bhi6ln2ut4ll3idw6bdk6ncqfkzrjkciocedago4irrzqvwba
    ONTO m1e5hi6ymifyqavmoos576n7n7obeqg2m5qe2dqcf6h2swjg5qo2ca
{
  ALTER TYPE default::Organization {
      CREATE MULTI LINK ancestors -> default::Organization {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
  ALTER TYPE default::Organization {
      ALTER LINK children {
          USING (.<ancestors[IS default::Organization]);
      };
  };
  ALTER TYPE default::User {
      ALTER LINK organizations {
          USING (.directly_organizations.<ancestors[IS default::Organization]);
      };
  };
  ALTER TYPE default::Organization {
      ALTER LINK users {
          USING (SELECT
              DISTINCT (((SELECT
                  .directly_users
              ) UNION (SELECT
                  .<ancestors[IS default::Organization].directly_users
              )))
          );
      };
  };
  ALTER TYPE default::Department {
      ALTER LINK ancestors {
          RESET CARDINALITY;
      };
  };
  ALTER TYPE default::Organization {
      ALTER PROPERTY hierarchy {
          USING (std::count(.ancestors));
      };
  };
  ALTER TYPE default::Department {
      ALTER LINK ancestors {
          DROP OWNED;
          RESET TYPE;
      };
  };
  UPDATE Enterprise SET {
      ancestors += (
          SELECT detached OrganizationType
          FILTER .id = Enterprise.org_type.id
      )
  };
  UPDATE Department SET {
      ancestors += (
          SELECT detached OrganizationType
          FILTER .id = Department.enterprise.org_type.id
      )
  };
};
