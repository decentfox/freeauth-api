WITH
    account := <str>$account,
    code_type := <auth::VerifyCodeType>$code_type,
    code := <str>$code
SELECT (
    INSERT auth::VerifyRecord {
        account := account,
        code_type := code_type,
        code := code
    }
);
