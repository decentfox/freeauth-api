module default {
    type OrganizationType extending SoftDeletable {
        required property name -> str;
        property description -> str;
        required property is_protected -> bool {
            default := false
        };
        required property code -> str;
        required property code_upper := str_upper(.code);

        multi link enterprises := .<org_type[is Enterprise];

        constraint exclusive on (.code_upper);
    }

    abstract type Organization extending TimeStamped {
        required property name -> str;
        property code -> str;
        property code_upper := str_upper(.code);

        multi link children := .<parent[is Department];
    }

    type Enterprise extending Organization {
        property tax_id -> str;
        property issuing_bank -> str;
        property bank_account_number -> str;
        property contact_address -> str;
        property contact_phone_num -> str;

        required link org_type -> OrganizationType {
            on target delete delete source;
        }

        constraint exclusive on ( (.code_upper, .org_type) );
    }

    type Department extending Organization {
        property description -> str;

        required link enterprise -> Enterprise;
        required link parent -> Organization {
            on target delete delete source;
        };

        constraint exclusive on ( (.code_upper, .enterprise) );
    }
}
