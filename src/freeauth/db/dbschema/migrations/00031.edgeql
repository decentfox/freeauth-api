CREATE MIGRATION m1h6dswlrws7hmb5pp5bdfr3k45b5gpmb37ce5ucfeu6xyfbnw3ycq
    ONTO m1dgr62tchpeuhcn27rkeaqtdne4emmettqbtn5ekurarjkyg57q5a
{
  ALTER TYPE auth::AuditLog {
      ALTER LINK user {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
  ALTER TYPE auth::Token {
      ALTER LINK user {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
};
