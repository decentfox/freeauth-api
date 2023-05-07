from __future__ import annotations

import uuid
from typing import List

from pydantic import EmailStr, Field, root_validator, validator
from pydantic.dataclasses import dataclass

from ..dataclasses import BaseModelConfig
from ..utils import MOBILE_REGEX


class UserBodyConfig(BaseModelConfig):
    error_msg_templates = {
        "value_error.any_str.max_length": (
            "最大支持的长度为{limit_value}个字符"
        ),
        "value_error.email": "邮箱格式有误",
        "value_error.str.regex": "仅支持中国大陆11位手机号",
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
        "type_error.uuid": "ID格式错误",
    }


@dataclass(config=UserBodyConfig)
class UserPostBody:
    name: str | None = Field(
        None,
        title="姓名",
        description="用户姓名（选填），默认为用户名",
        max_length=50,
    )
    username: str | None = Field(
        None,
        title="用户名",
        description="登录用户名，未提供则由随机生成",
        max_length=50,
    )
    email: EmailStr | None = Field(
        None, description="邮箱，可接收登录验证邮件", title="邮箱"
    )
    mobile: str | None = Field(
        None,
        title="手机号",
        description="仅支持中国大陆11位手机号码，可接收短信验证邮件",
        regex=MOBILE_REGEX,
    )
    organization_ids: list[uuid.UUID] | None = Field(
        None,
        title="直属部门 ID 列表",
        description="可设置一个或多个部门分支或企业机构 ID",
    )

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    @root_validator
    def validate_username_or_email_or_mobile(cls, values):
        username, email, mobile = (
            values.get("username"),
            values.get("email"),
            values.get("mobile"),
        )
        if not (username or email or mobile):
            raise ValueError("用户名、邮箱、手机号三个信息中请至少提供一项")
        return values


@dataclass(config=UserBodyConfig)
class UserPutBody:
    name: str = Field(
        ...,
        title="姓名",
        description="用户姓名",
        max_length=50,
    )
    username: str = Field(
        ...,
        title="用户名",
        description="登录用户名",
        max_length=50,
    )
    email: EmailStr | None = Field(
        None, description="邮箱，可接收登录验证邮件", title="邮箱"
    )
    mobile: str | None = Field(
        None,
        title="手机号",
        description="仅支持中国大陆11位手机号码，可接收短信验证邮件",
        regex=MOBILE_REGEX,
    )


@dataclass(config=BaseModelConfig)
class UserOrganizationBody:
    organization_ids: list[uuid.UUID] = Field(
        ...,
        title="直属部门 ID 列表",
        description="可设置一个或多个部门分支或企业机构 ID",
        min_items=1,
    )


@dataclass(config=BaseModelConfig)
class UserResignationBody:
    user_ids: list[uuid.UUID] = Field(
        ...,
        title="用户 ID 列表",
        description="待离职的用户 ID 列表",
    )
    is_deleted: bool | None = Field(
        None,
        title="是否禁用",
        description="true 为禁用用户，false 为启用用户",
    )


@dataclass(config=UserBodyConfig)
class UserStatusBody:
    user_ids: List[uuid.UUID] = Field(
        ...,
        title="用户 ID 数组",
        description="待变更状态的用户 ID 列表",
    )
    is_deleted: bool = Field(
        ...,
        title="是否禁用",
        description="true 为禁用用户，false 为启用用户",
    )


@dataclass(config=UserBodyConfig)
class UserDeleteBody:
    user_ids: List[uuid.UUID] = Field(
        ...,
        title="用户 ID 数组",
        description="待删除的用户 ID 列表",
    )
