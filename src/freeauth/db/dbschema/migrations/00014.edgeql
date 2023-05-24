CREATE MIGRATION m1qwqxduinfru3jpz46hrkbcrzhywg5jrueyq25heou42yvbb4jxoa
    ONTO m1vdfct3jlfeag4dpsn7uc6u757owft6zkxarphwt65xtughmbqjrq
{
  ALTER TYPE default::Department {
      CREATE MULTI LINK ancestors -> default::Organization {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
  ALTER TYPE default::Organization {
      ALTER LINK children {
          USING (.<ancestors[IS default::Department]);
      };
  };
  ALTER TYPE default::User {
      CREATE MULTI LINK directly_organizations -> default::Organization {
          ON TARGET DELETE ALLOW;
      };
  };
  UPDATE default::User SET {
      directly_organizations := .org_branches
  };
  ALTER TYPE default::User {
      CREATE MULTI LINK organizations := (.directly_organizations.<ancestors[IS default::Department]);
  };
  ALTER TYPE default::Organization {
      ALTER LINK directly_users {
          USING (.<directly_organizations[IS default::User]);
      };
  };
  ALTER TYPE default::Organization {
      ALTER LINK users {
          USING (SELECT
              DISTINCT (((SELECT
                  .directly_users
              ) UNION (SELECT
                  .<ancestors[IS default::Department].directly_users
              )))
          );
      };
  };
  ALTER TYPE default::Organization {
      CREATE MULTI LINK directly_children := (.<parent[IS default::Department]);
  };
  ALTER TYPE default::User {
      DROP LINK org_branches;
  };
};
