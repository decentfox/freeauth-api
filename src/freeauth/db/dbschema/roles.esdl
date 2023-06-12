module freeauth {
    type Role extending TimeStamped, SoftDeletable {
        required property name -> str;
        property code -> str;
        property code_upper := str_upper(.code);
        property description -> str;

        link org_type -> OrganizationType {
            on target delete delete source;
        };
        multi link users := .<roles[is User];
        multi link permissions -> Permission {
            on target delete allow;
        };

        constraint exclusive on (.code_upper);
    }
}
