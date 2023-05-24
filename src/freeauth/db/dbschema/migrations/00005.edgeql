CREATE MIGRATION m1dkkpaxgqcxdrgvns3jyabvqnhyfm3fq4uransv5kgbpo7eai74ia
    ONTO m1s2m5m5n3lfu2fef5xzxi2otaji72lytym6nynflas5sksmky4emq
{
  ALTER TYPE auth::VerifyRecord {
      DROP CONSTRAINT std::exclusive ON ((.account, .code, .code_type, .verify_type));
      CREATE REQUIRED PROPERTY consumable := (NOT (EXISTS (.consumed_at)));
      CREATE INDEX ON ((.account, .code_type, .verify_type, .consumable));
      CREATE INDEX ON (.code);
  };
};
