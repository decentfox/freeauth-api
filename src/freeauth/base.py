class BaseModelConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
    }
