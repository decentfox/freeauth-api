with
    id := <optional uuid>$id,
    code := <optional str>$code,
    org_type_id := <optional uuid>$org_type_id,
    org_type_code := <optional str>$org_type_code
select assert_single(
    (
        select freeauth::Enterprise {
            name,
            code,
            tax_id,
            issuing_bank,
            bank_account_number,
            contact_address,
            contact_phone_num
        }
        filter
            (.id = id) ??
            (.code ?= code and .org_type.id = org_type_id) ??
            (.code ?= code and .org_type.code = org_type_code)
    )
);
