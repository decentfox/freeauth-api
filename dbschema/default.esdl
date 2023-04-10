module default {
    abstract type TimeStamped {
        required property created_at -> datetime {
            readonly := true;
            default := datetime_of_transaction();
        }

        index on (.created_at);
    }
}
