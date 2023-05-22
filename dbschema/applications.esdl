module default {
    type Application extending TimeStamped, SoftDeletable {
        required property name -> str;
        property description -> str;
        property secret_key -> str;
        required property is_protected -> bool {
            default := false
        };

        multi link permissions := .<application[is Permission];
    }
}
