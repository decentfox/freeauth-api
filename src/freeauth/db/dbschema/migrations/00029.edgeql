CREATE MIGRATION m15uxqfrciueamevbih6r65vd434ageufssdazmq5fc733fr4plyza
    ONTO m1eblcf5pphm7ls5xzx3w7v6j46tttkufa7khahttim6wkn4np5taa
{
  ALTER TYPE default::Permission {
      CREATE MULTI LINK tags -> default::PermissionTag {
          ON TARGET DELETE ALLOW;
      };
  };
};
