CREATE MIGRATION m1fsyw67kjxelqp46j4x353oivbl3re5oo2mac3kn5l2xxdzikvvxa
    ONTO m1xv4bhi6ln2ut4ll3idw6bdk6ncqfkzrjkciocedago4irrzqvwba
{
  ALTER TYPE default::User {
      CREATE MULTI LINK roles -> default::Role {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE default::Role {
      CREATE MULTI LINK users := (.<roles[IS default::User]);
  };
};
