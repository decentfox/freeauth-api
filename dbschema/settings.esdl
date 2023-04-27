module default {
    type LoginSetting {
        required property key -> str {
            constraint exclusive;
        };
        required property value -> str;

        index on (.key);
    };
}
