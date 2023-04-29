module default {
    type OrganizationType extending SoftDeletable {
        required property name -> str;
        property description -> str;
        required property is_protected -> bool {
            default := false
        };
    }
}
