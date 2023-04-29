CREATE MIGRATION m1v7kijuudrt2n6kttcv5ohwnmu4wxgr7qmlffx3pi27cjuwql3uma
    ONTO m1aotx76nsod5ol5ijpfbdt3rjokip2ph5anfji2vseprsvfsfaw7a
{
  CREATE TYPE default::OrganizationType EXTENDING default::SoftDeletable {
      CREATE PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY is_protected -> std::bool {
          SET default := false;
      };
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  INSERT default::OrganizationType {
      name := '内部组织',
      is_protected := true
  };
};
