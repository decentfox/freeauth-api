CREATE MIGRATION m12xdspp5ampvt7ycdyizuv4gr7qw57wuy2mfi3fsoipvyk7txti2a
    ONTO m17uiwcmjgs2uxxgcfi3qb2ddqijuoencbr74xc42cqiq7esqnnr6q
{
  ALTER TYPE default::User {
      CREATE PROPERTY reset_pwd_on_next_login -> std::bool {
          SET default := false;
      };
  };
  ALTER SCALAR TYPE auth::AuditEventType EXTENDING enum<SignIn, SignOut, SignUp, ResetPwd>;
};
