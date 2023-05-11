CREATE MIGRATION m1fhh6hqsmblbhx6f5ymfuirfafd77p5h5qn2r3655t3ama6otydlq
    ONTO m1fsyw67kjxelqp46j4x353oivbl3re5oo2mac3kn5l2xxdzikvvxa
{
  ALTER TYPE default::User {
      CREATE LINK org_type -> default::OrganizationType {
          ON TARGET DELETE ALLOW;
      };
  };
  UPDATE default::User SET {
      org_type := (
          SELECT .directly_organizations.ancestors[is OrganizationType]
          UNION .directly_organizations[is OrganizationType]
          LIMIT 1
      )
  };
  ALTER TYPE default::Role {
      CREATE LINK org_type -> default::OrganizationType {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
  ALTER TYPE default::OrganizationType {
      CREATE MULTI LINK roles := (.<org_type[IS default::Role]);
  };
  UPDATE default::Role SET {
      org_type := (
          SELECT .organizations.ancestors[is OrganizationType]
          UNION .organizations[is OrganizationType]
          LIMIT 1
      )
  };
  ALTER TYPE default::Role {
      DROP LINK organizations;
  };
  UPDATE default::User FILTER EXISTS .org_type SET {
      roles -= (
          SELECT .roles FILTER .org_type != default::User.org_type
      ),
      directly_organizations -= (
          SELECT .directly_organizations[is OrganizationType]
          UNION (
            SELECT .directly_organizations
            FILTER default::User.org_type NOT IN .ancestors
          )
      )
  };
};
