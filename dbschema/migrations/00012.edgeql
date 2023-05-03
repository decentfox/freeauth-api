CREATE MIGRATION m15hmnxkaga5fnk63kzxzhektacqex3h5xz4afnlkhz7zcmeolvbbq
    ONTO m1bmljoubai5lk632o7ubp2pmfaltqbzust5aulzlwmbdwhngpmycq
{
  ALTER TYPE default::Department {
      ALTER LINK enterprise {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
};
