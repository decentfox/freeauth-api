# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan
# PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from __future__ import annotations

import re

from pydantic import EmailStr, Field, validator
from pydantic.dataclasses import dataclass

from freeauth.db.auth.auth_qry_async_edgeql import FreeauthCodeType
from freeauth.security.utils import MOBILE_REGEX

from ..dataclasses import BaseModelConfig
from ..validators import MobileStr, UsernameStr


@dataclass(config=BaseModelConfig)
class SignUpSendCodeBody:
    code_type: FreeauthCodeType = Field(..., title="验证码类型")
    account: str = Field(
        ...,
        title="注册账号",
        description="手机号或邮箱",
    )

    @validator("account")
    def validate_account(cls, v, values):
        code_type = values.get("code_type")
        if code_type == FreeauthCodeType.SMS:
            if not re.match(MOBILE_REGEX, v):
                raise ValueError("仅支持中国大陆11位手机号")
        elif code_type == FreeauthCodeType.EMAIL:
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


@dataclass(config=BaseModelConfig)
class ResetPwdBody:
    password: str = Field(
        ...,
        title="新登录密码",
        description="新登录密码",
    )


@dataclass(config=BaseModelConfig)
class UpdateProfileBody:
    name: str = Field(
        ...,
        title="姓名",
        description="用户姓名",
        min_length=1,
        max_length=50,
    )
    username: UsernameStr = Field(
        ...,
        title="用户名",
        description="登录用户名",
    )
    email: EmailStr | None = Field(
        None, description="邮箱，可接收登录验证邮件", title="邮箱"
    )
    mobile: MobileStr | None = Field(
        None,
        title="手机号",
        description="仅支持中国大陆11位手机号码，可接收短信验证邮件",
    )

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v
