WITH
    id := <optional uuid>$id,
    code := <optional str>$code
SELECT assert_single(
    (
        SELECT
        Enterprise {
            name,
            code,
            tax_id,
            issuing_bank,
            bank_account_number,
            contact_address,
            contact_phone_num
        }
        FILTER .id = id IF EXISTS id ELSE .code ?= code
    )
);
