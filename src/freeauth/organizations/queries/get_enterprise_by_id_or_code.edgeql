WITH
    id := <optional uuid>$id,
    code := <optional str>$code,
    org_type_id := <optional uuid>$org_type_id,
    org_type_code := <optional str>$org_type_code
SELECT assert_single(
    (
        SELECT Enterprise {
            name,
            code,
            tax_id,
            issuing_bank,
            bank_account_number,
            contact_address,
            contact_phone_num
        }
        FILTER
            (.id = id) ??
            (.code ?= code AND .org_type.id = org_type_id) ??
            (.code ?= code AND .org_type.code = org_type_code)
        )
    )
);
