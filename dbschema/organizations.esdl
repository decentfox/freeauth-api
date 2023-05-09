module default {
    type OrganizationType extending Organization, SoftDeletable {
        property description -> str;
        required property is_protected -> bool {
            default := false
        };

        multi link enterprises := .<org_type[is Enterprise];

        constraint exclusive on (.code_upper);
    }

    abstract type Organization extending TimeStamped {
        required property name -> str;
        property code -> str;
        property code_upper := str_upper(.code);
        required property hierarchy := count(.ancestors);

        multi link directly_children := .<parent[is Department];
        multi link children := .<ancestors[is Organization];
        multi link directly_users := .<directly_organizations[is User];
        multi link users := (
            SELECT DISTINCT (
                (
                    SELECT .directly_users
                ) UNION (
                    SELECT .<ancestors[is Organization].directly_users
                )
            )
        );
        multi link ancestors -> Organization {
            on target delete delete source;
        };
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

        required link enterprise -> Enterprise {
            on target delete delete source;
        };
        required link parent -> Organization {
            on target delete delete source;
        };

        constraint exclusive on ( (.code_upper, .enterprise) );
    }
}
