with
    module freeauth,
    id := <optional uuid>$id,
    current_code := <optional str>$current_code,
    org_type_id := <optional uuid>$org_type_id,
    org_type_code := <optional str>$org_type_code,
    enterprise := assert_single((
        select Enterprise
        filter
            (.id = id) ??
            (.code ?= current_code and .org_type.id = org_type_id) ??
            (
                .code ?= current_code and
                .org_type.code = org_type_code
            ) ??
            false
    ))
select (
    UPDATE enterprise
    set {
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
