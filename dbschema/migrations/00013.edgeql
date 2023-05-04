CREATE MIGRATION m1vdfct3jlfeag4dpsn7uc6u757owft6zkxarphwt65xtughmbqjrq
    ONTO m15hmnxkaga5fnk63kzxzhektacqex3h5xz4afnlkhz7zcmeolvbbq
{
  ALTER TYPE default::User {
      CREATE MULTI LINK org_branches -> default::Organization {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE default::Organization {
      CREATE MULTI LINK directly_users := (.<org_branches[IS default::User]);
  };
  ALTER TYPE default::Organization {
      CREATE MULTI LINK users := (SELECT
          DISTINCT (((SELECT
              .directly_users
          ) UNION (SELECT
              .children.directly_users
          )))
      );
  };
};
