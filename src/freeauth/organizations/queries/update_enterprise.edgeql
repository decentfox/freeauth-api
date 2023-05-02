WITH
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    enterprise := assert_single((
        SELECT Enterprise FILTER (
            .id = id IF EXISTS id ELSE .code ?= current_code
        )
    ))
SELECT (
    UPDATE enterprise
    SET {
        name := <str>$name,
        code := <optional str>$code,
        tax_id := <optional str>$tax_id,
        issuing_bank := <optional str>$issuing_bank,
        bank_account_number := <optional str>$bank_account_number,
        contact_address := <optional str>$contact_address,
        contact_phone_num := <optional str>$contact_phone_num,
    }
) {
    name,
    code,
    tax_id,
    issuing_bank,
    bank_account_number,
    contact_address,
    contact_phone_num
};