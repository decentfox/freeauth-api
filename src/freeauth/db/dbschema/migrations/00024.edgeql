CREATE MIGRATION m1pwk6wff5r2xbxtjeesr6x76xw6wksmmvmeqlt6rkczev3z4ch7wq
    ONTO m1jqxiptf66zakhlguijkgmp2fbjlar2fqrsq7d3gfsyx2tvbe7ica
{
  ALTER TYPE default::Permission {
      CREATE MULTI LINK tags -> default::Tag {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE default::Tag {
      ALTER PROPERTY name {
          CREATE CONSTRAINT std::exclusive;
      };
  };
};
