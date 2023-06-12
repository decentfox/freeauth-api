with
    module freeauth,
    org_type := (
        select OrganizationType filter .id = <uuid>$org_type_id
    )
for _ in (
    select true filter exists org_type
) union (
    select (
        insert Enterprise {
            name := <str>$name,
            code := <optional str>$code,
            tax_id := <optional str>$tax_id,
            issuing_bank := <optional str>$issuing_bank,
            bank_account_number := <optional str>$bank_account_number,
            contact_address := <optional str>$contact_address,
            contact_phone_num := <optional str>$contact_phone_num,
            org_type := org_type,
            ancestors := ( select org_type )
        }
    ) {
        name,
        code,
        tax_id,
        issuing_bank,
        bank_account_number,
        contact_address,
        contact_phone_num
    }
);
