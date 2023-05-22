from __future__ import annotations

import re

from pydantic.validators import anystr_strip_whitespace, str_validator

from .utils import MOBILE_REGEX


class StrValidator(str):
    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield anystr_strip_whitespace
        yield cls.validate

    @classmethod
    def validate(cls, value: str):
        raise NotImplementedError


class MobileStr(StrValidator):
    regex = re.compile(MOBILE_REGEX)

    @classmethod
    def validate(cls, value: str | MobileStr) -> MobileStr:
        if not cls.regex.match(value):
            raise ValueError("仅支持中国大陆11位手机号")
        return cls(value)


class UsernameStr(StrValidator):
    regex = re.compile(r"^(?![0-9])[^@]{1,50}$")

    @classmethod
    def validate(cls, value: str | UsernameStr) -> UsernameStr:
        if not cls.regex.match(value):
            raise ValueError(
                "用户名不能以数字开头，不得包含@符号，最大支持的长度为50个字符"
            )
        return cls(value)
