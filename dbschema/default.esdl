module default {
    abstract type TimeStamped {
        required property created_at -> datetime {
            readonly := true;
            default := datetime_of_transaction();
        }

        index on (.created_at);
    }

    abstract type SoftDeletable {
        property deleted_at -> datetime;
        property is_deleted := exists .deleted_at;

        index on (.is_deleted);
    }
}
