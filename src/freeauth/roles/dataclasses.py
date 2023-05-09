from __future__ import annotations

import uuid
from enum import Enum

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

from ..dataclasses import BaseModelConfig


@dataclass(config=BaseModelConfig)
class RolePostBody:
    name: str = Field(
        ...,
        title="名称",
        description="角色名称",
        min_length=1,
    )
    code: str | None = Field(
        None,
        title="代码",
        description="角色代码",
    )
    description: str | None = Field(
        None,
        title="描述",
        description="角色描述",
    )
    organization_ids: list[uuid.UUID] | None = Field(
        None,
        title="归属对象 ID 列表",
        description="可设置一个或多个组织类型、部门分支或企业机构 ID",
    )

    @validator("code", pre=True)
    def convert_to_uppercase(cls, v):
        return v.upper() if v else v


@dataclass(config=BaseModelConfig)
class RolePutBody(RolePostBody):
    is_deleted: bool | None = Field(
        None,
        title="是否禁用",
        description="true 为禁用角色，false 为启用角色；该字段为空时，不做任何更新",
    )


@dataclass(config=BaseModelConfig)
class RoleStatusBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="角色 ID 列表",
        description="待变更状态的角色 ID 列表",
        min_items=1,
    )
    is_deleted: bool = Field(
        ...,
        title="是否禁用",
        description="true 为禁用角色类型，false 为启用角色类型",
    )


@dataclass(config=BaseModelConfig)
class RoleDeleteBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="角色 ID 列表",
        description="待删除的角色 ID 列表",
    )


class RoleTypeEnum(str, Enum):
    global_role = "global"
    org_type = "org_type"
    enterprise = "enterprise"
    department = "department"


@dataclass(config=BaseModelConfig)
class OrganizationRoleQueryBody:
    q: str | None = Field(
        None,
        title="搜索关键字",
        description="支持搜索角色名称、角色代码、角色描述",
    )
    role_type: RoleTypeEnum | None = Field(
        None,
        title="角色类型",
        description="支持按角色类型进行过滤",
    )
    is_deleted: bool | None = Field(
        None,
        title="角色是否禁用",
        description=(
            "支持按角色状态进行过滤，true 代表已禁用的角色，false 代表已启用的角色"
        ),
    )
