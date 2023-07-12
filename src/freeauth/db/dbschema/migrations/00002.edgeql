CREATE MIGRATION m1wvgzip4yettq2h77fv35tivc2e2dowidwq74acnh7kc5fuupdkla
    ONTO m1tbegoksyubjz3i64c5grkdxzzrudz4664qpr72pg7zcxj223k66q
{
  ALTER TYPE freeauth::Role {
      CREATE PROPERTY is_protected := (std::any(((SELECT
          freeauth::Permission
      FILTER
          ((EXISTS (.application) AND .application.is_protected) AND (.code = '*'))
      ) IN .permissions)));
  };
};
