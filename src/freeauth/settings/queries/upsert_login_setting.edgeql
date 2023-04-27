WITH
    key := <str>$key,
    value := <str>$value
SELECT (
    INSERT LoginSetting {
        key := key,
        value := value
    } UNLESS CONFLICT ON (.key) ELSE (
        UPDATE LoginSetting SET { value := value}
    )
) { key, value };
