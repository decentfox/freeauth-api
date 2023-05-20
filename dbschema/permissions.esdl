module default {
    type Permission extending TimeStamped, SoftDeletable {
        required property name -> str;
        required property code -> str;
        property code_upper := str_upper(.code);
        property description -> str;

        required link application -> Application {
            on target delete delete source;
        };
        multi link roles := .<permissions[is Role];

        constraint exclusive on (.code_upper)
    }
}
