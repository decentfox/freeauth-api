FOR x IN json_object_unpack(<json>$configs)
UNION (
    INSERT LoginSetting {
        key := x.0,
        value := to_str(x.1)
    } UNLESS CONFLICT ON (.key) ELSE (
        UPDATE LoginSetting SET { value := to_str(x.1)}
    )
);
