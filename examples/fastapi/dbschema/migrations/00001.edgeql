CREATE MIGRATION m1omzqtpzkn2bm4zl56vjh2zereitazqa34xyys3f4ldog5ps6sksa
    ONTO initial
{
  CREATE TYPE default::Person {
      CREATE REQUIRED PROPERTY name: std::str;
  };
  CREATE TYPE default::Movie {
      CREATE REQUIRED LINK director: default::Person;
      CREATE REQUIRED PROPERTY title: std::str;
  };
};
