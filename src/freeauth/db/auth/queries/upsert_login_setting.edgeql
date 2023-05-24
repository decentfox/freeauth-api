for x in json_object_unpack(<json>$configs)
union (
    insert LoginSetting {
        key := x.0,
        value := to_str(x.1)
    } unless conflict on (.key) else (
        update LoginSetting set { value := to_str(x.1)}
    )
);
