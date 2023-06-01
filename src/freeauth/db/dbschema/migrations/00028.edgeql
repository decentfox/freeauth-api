CREATE MIGRATION m1eblcf5pphm7ls5xzx3w7v6j46tttkufa7khahttim6wkn4np5taa
    ONTO m1p6xq2d26qoatklmtopthexwf7gqlr2qfpv7x3jgf3hyj4nnjjepa
{
  ALTER TYPE default::Permission {
      DROP LINK tags;
  };
};
