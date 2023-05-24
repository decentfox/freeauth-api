CREATE MIGRATION m1u4ogrpaes2irqcrqrvjhawbhoehnabnjviqcyzumxknee6lhx4la
    ONTO m1qwqxduinfru3jpz46hrkbcrzhywg5jrueyq25heou42yvbb4jxoa
{
  ALTER TYPE default::Organization {
      CREATE REQUIRED PROPERTY hierarchy := (std::count([IS default::Department].ancestors));
  };
};
