CREATE MIGRATION m1jqxiptf66zakhlguijkgmp2fbjlar2fqrsq7d3gfsyx2tvbe7ica
    ONTO m1ab5gxxhogfx6h4x3t76fh4x4go52xk7pujr2iyjdsglpgaktlmiq
{
  CREATE TYPE default::Application EXTENDING default::TimeStamped, default::SoftDeletable {
      CREATE PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY is_protected -> std::bool {
          SET default := false;
      };
      CREATE REQUIRED PROPERTY name -> std::str;
      CREATE PROPERTY secret_key -> std::str;
  };
  INSERT default::Application {
      name := '默认应用',
      description := '即对接 FreeAuth 的应用。可更名本应用，也可创建新应用',
      is_protected := true
  };
  ALTER TYPE default::Permission {
      CREATE REQUIRED LINK application -> default::Application {
          ON TARGET DELETE DELETE SOURCE;
          SET REQUIRED USING (std::assert_exists((SELECT
              default::Application 
          LIMIT
              1
          )));
      };
  };
  ALTER TYPE default::Application {
      CREATE MULTI LINK permissions := (.<application[IS default::Permission]);
  };
  CREATE SCALAR TYPE default::TagType EXTENDING enum<Permission>;
  CREATE TYPE default::Tag EXTENDING default::TimeStamped {
      CREATE REQUIRED PROPERTY name -> std::str;
      CREATE REQUIRED PROPERTY tag_type -> default::TagType {
          SET readonly := true;
      };
  };
};
