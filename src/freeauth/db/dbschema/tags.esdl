module default {
    abstract type Tag extending TimeStamped {
        required property name -> str;
        property rank -> int16;
    }

    type PermissionTag extending Tag {
        constraint exclusive on (.name);
    }
}
