for x in json_object_unpack(<json>$configs)
union (
    insert freeauth::LoginSetting {
        key := x.0,
        value := to_str(x.1)
    } unless conflict on (.key) else (
        update freeauth::LoginSetting set { value := to_str(x.1)}
    )
);
