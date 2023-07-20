CREATE MIGRATION m1o7p4knsqfmeuxbywr3ev52flukr5qhmciwhc53ubzmejm25t2t2q
    ONTO m1wvgzip4yettq2h77fv35tivc2e2dowidwq74acnh7kc5fuupdkla
{
  ALTER SCALAR TYPE freeauth::AuditEventType EXTENDING enum<SignIn, SignOut, SignUp, ResetPwd, ChangePwd>;
};
