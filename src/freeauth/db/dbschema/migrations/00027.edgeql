CREATE MIGRATION m1p6xq2d26qoatklmtopthexwf7gqlr2qfpv7x3jgf3hyj4nnjjepa
    ONTO m12xdspp5ampvt7ycdyizuv4gr7qw57wuy2mfi3fsoipvyk7txti2a
{
  DELETE default::Tag;
  ALTER TYPE default::Tag {
      SET ABSTRACT;
      CREATE PROPERTY rank -> std::int16;
      ALTER PROPERTY name {
          DROP CONSTRAINT std::exclusive;
      };
  };
  CREATE TYPE default::PermissionTag EXTENDING default::Tag {
      CREATE CONSTRAINT std::exclusive ON (.name);
  };
  ALTER TYPE default::Tag {
      DROP PROPERTY tag_type;
  };
  DROP SCALAR TYPE default::TagType;
};
