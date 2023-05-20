CREATE MIGRATION m1ab5gxxhogfx6h4x3t76fh4x4go52xk7pujr2iyjdsglpgaktlmiq
    ONTO m1gdb7pc5d5ecwytpjgimgq3m5axq7jz3uwtsemnwk37ihkh2x5vvq
{
  ALTER TYPE default::Permission {
      ALTER PROPERTY code {
          SET REQUIRED USING ('CODE');
      };
  };
};
