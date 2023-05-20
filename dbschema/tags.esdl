module default {
    scalar type TagType extending enum<Permission>;

    type Tag extending TimeStamped {
        required property name -> str;
        required property tag_type -> TagType {
            readonly := true;
        };
    }
}
