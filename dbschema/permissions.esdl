module freeauth {
    type Permission extending TimeStamped, SoftDeletable {
        required property name -> str;
        required property code -> str;
        property code_upper := str_upper(.code);
        property description -> str;

        required link application -> Application {
            on target delete delete source;
        };
        multi link roles := .<permissions[is Role];
        multi link tags -> PermissionTag {
            on target delete allow;
        };

        constraint exclusive on ( (.code_upper, .application) );

        access policy full_access
            allow all;
        access policy readonly_wildcard_perm
            deny delete, update
            using (.code = '*');
    }
}
