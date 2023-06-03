CREATE MIGRATION m1dgr62tchpeuhcn27rkeaqtdne4emmettqbtn5ekurarjkyg57q5a
    ONTO m15uxqfrciueamevbih6r65vd434ageufssdazmq5fc733fr4plyza
{
  ALTER TYPE default::Permission {
      CREATE ACCESS POLICY full_access
          ALLOW ALL ;
      CREATE ACCESS POLICY readonly_wildcard_perm
          DENY UPDATE, DELETE USING ((.code = '*'));
  };
  insert default::Permission {
      name := '通配符权限',
      code := '*',
      description := '通配符权限授予应用的所有访问权限',
      application := assert_single((
          select default::Application filter .is_protected
      ))
  };
};
