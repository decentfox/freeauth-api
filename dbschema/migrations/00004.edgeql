CREATE MIGRATION m1qr3p7gikxcfkzg7qilq33ty5acuj3njvdkqvjt3kuvg7kevrenzq
    ONTO m1o7p4knsqfmeuxbywr3ev52flukr5qhmciwhc53ubzmejm25t2t2q
{
  DROP FUTURE nonrecursive_access_policies;
  ALTER TYPE freeauth::AuditLog {
      CREATE INDEX ON (.status_code);
  };
};
