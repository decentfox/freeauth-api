WITH
    org_type := (
        SELECT OrganizationType FILTER .id = <uuid>$org_type_id
    )
FOR _ IN (
    SELECT true FILTER EXISTS org_type
) UNION (
    SELECT (
        INSERT Enterprise {
            name := <str>$name,
            code := <optional str>$code,
            tax_id := <optional str>$tax_id,
            issuing_bank := <optional str>$issuing_bank,
            bank_account_number := <optional str>$bank_account_number,
            contact_address := <optional str>$contact_address,
            contact_phone_num := <optional str>$contact_phone_num,
            org_type := org_type,
            ancestors := ( SELECT org_type )
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
