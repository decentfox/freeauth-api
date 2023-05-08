from __future__ import annotations

import re

from pydantic import EmailStr, Field, validator
from pydantic.dataclasses import dataclass

from ..dataclasses import BaseModelConfig
from ..query_api import AuthCodeType
from ..utils import MOBILE_REGEX


@dataclass(config=BaseModelConfig)
class SignUpSendCodeBody:
    code_type: AuthCodeType = Field(..., title="验证码类型")
    account: str = Field(
        ...,
        title="注册账号",
        description="手机号或邮箱",
    )

    @validator("account")
    def validate_account(cls, v, values):
        code_type = values.get("code_type")
        if code_type == AuthCodeType.SMS:
            if not re.match(MOBILE_REGEX, v):
                raise ValueError("仅支持中国大陆11位手机号")
        elif code_type == AuthCodeType.EMAIL:
            try:
                EmailStr.validate(v)
            except ValueError:
                raise ValueError("邮箱格式有误")
        else:
            raise ValueError("手机号码或邮箱格式有误")
        return v


@dataclass(config=BaseModelConfig)
class SignUpBody(SignUpSendCodeBody):
    code: str = Field(
        ...,
        title="注册验证码",
        description="通过短信或邮件发送的注册验证码",
    )


@dataclass(config=BaseModelConfig)
class SignInSendCodeBody:
    account: str = Field(
        ...,
        title="登录账号",
        description="手机号或邮箱",
    )

    @validator("account")
    def validate_account(cls, v):
        if not re.match(MOBILE_REGEX, v):
            try:
                EmailStr.validate(v)
            except ValueError:
                raise ValueError("手机号码或邮箱格式有误")
        return v


@dataclass(config=BaseModelConfig)
class SignInCodeBody(SignInSendCodeBody):
    code: str = Field(
        ...,
        title="登录验证码",
        description="通过短信或邮件发送的登录验证码",
    )


@dataclass(config=BaseModelConfig)
class SignInPwdBody:
    account: str = Field(
        ...,
        title="登录账号",
        description="用户名或手机号或邮箱",
    )
    password: str = Field(
        ...,
        title="登录密码",
        description="登录密码",
    )
