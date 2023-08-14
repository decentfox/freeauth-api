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

import uuid
from typing import List

from pydantic import EmailStr, Field, root_validator, validator
from pydantic.dataclasses import dataclass

from ..dataclasses import FilterItem  # noqa
from ..dataclasses import BaseModelConfig, QueryBody
from ..validators import MobileStr, UsernameStr


@dataclass(config=BaseModelConfig)
class UserPostBody:
    name: str | None = Field(
        None,
        title="姓名",
        description="用户姓名（选填），默认为用户名",
        max_length=50,
    )
    username: UsernameStr | None = Field(
        None,
        title="用户名",
        description="登录用户名，未提供则由随机生成",
    )
    email: EmailStr | None = Field(
        None, description="邮箱，可接收登录验证邮件", title="邮箱"
    )
    mobile: MobileStr | None = Field(
        None,
        title="手机号",
        description="仅支持中国大陆11位手机号码，可接收短信验证邮件",
    )
    password: str | None = Field(
        None,
        title="密码",
        description="初始密码，如未提供则由系统自动生成",
    )
    organization_ids: list[uuid.UUID] | None = Field(
        None,
        title="直属部门 ID 列表",
        description="可设置一个或多个部门分支或企业机构 ID",
    )
    org_type_id: uuid.UUID | None = Field(
        None,
        title="组织类型 ID",
        description="用户所属组织类型",
    )
    reset_pwd_on_first_login: bool = Field(
        False,
        title="是否强制用户在首次登录时修改密码",
        description="默认不强制",
    )
    send_first_login_email: bool = Field(
        False,
        title="是否通过邮件发送初始默认登录信息",
        description="默认不发送",
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


@dataclass(config=BaseModelConfig)
class UserPutBody:
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


@dataclass(config=BaseModelConfig)
class UserOrganizationBody:
    organization_ids: list[uuid.UUID] = Field(
        ...,
        title="直属部门 ID 列表",
        description="可设置一个或多个部门分支或企业机构 ID",
        min_items=1,
    )
    org_type_id: uuid.UUID | None = Field(
        None,
        title="组织类型 ID",
        description="用户所属组织类型",
    )


@dataclass(config=BaseModelConfig)
class UserRoleBody:
    role_ids: list[uuid.UUID] = Field(
        ...,
        title="角色 ID 列表",
        description="可设置一个或多个角色，或清空",
    )


@dataclass(config=BaseModelConfig)
class UserResignationBody:
    user_ids: list[uuid.UUID] = Field(
        ...,
        title="用户 ID 列表",
        description="待离职的用户 ID 列表",
    )
    is_deleted: bool | None = Field(
        False,
        title="是否禁用",
        description="true 为禁用用户，false 保持不变",
    )


@dataclass(config=BaseModelConfig)
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


@dataclass(config=BaseModelConfig)
class UserDeleteBody:
    user_ids: List[uuid.UUID] = Field(
        ...,
        title="用户 ID 数组",
        description="待删除的用户 ID 列表",
    )


@dataclass(config=BaseModelConfig)
class UserQueryBody(QueryBody):
    org_type_id: uuid.UUID | None = Field(
        None,
        title="组织类型 ID",
        description="支持过滤指定组织类型下的用户",
    )
    include_unassigned_users: bool = Field(
        True,
        title="是否包含未设置任何组织类型的用户",
        description="默认为 true，设为 false 代表仅查询关联了组织类型的用户",
    )
