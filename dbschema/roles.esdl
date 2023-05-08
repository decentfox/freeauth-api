module default {
    type Role extending TimeStamped, SoftDeletable {
        required property name -> str;
        property code -> str;
        property code_upper := str_upper(.code);
        property description -> str;

        multi link organizations -> Organization {
            on target delete allow;
        };

        constraint exclusive on (.code_upper);
    }
}
