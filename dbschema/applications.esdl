module freeauth {
    global current_app_id -> uuid;
    global current_app := (
        select Application filter .id = global current_app_id
    );

    type Application extending TimeStamped, SoftDeletable {
        required property name -> str;
        property description -> str;
        property hashed_secret -> str;
        required property is_protected -> bool {
            default := false
        };

        multi link permissions := .<application[is Permission];
    }
}
