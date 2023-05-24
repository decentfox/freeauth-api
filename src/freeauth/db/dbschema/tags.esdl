module default {
    scalar type TagType extending enum<Permission>;

    type Tag extending TimeStamped {
        required property name -> str {
            constraint exclusive;
        };
        required property tag_type -> TagType {
            readonly := true;
        };
    }
}
