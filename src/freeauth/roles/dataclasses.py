from __future__ import annotations

import uuid

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

from ..dataclasses import FilterItem  # noqa
from ..dataclasses import BaseModelConfig, QueryBody


@dataclass(config=BaseModelConfig)
class BaseRoleBody:
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

    @validator("code", pre=True)
    def convert_to_uppercase(cls, v):
        return v.upper() if v else v


@dataclass(config=BaseModelConfig)
class RolePostBody(BaseRoleBody):
    org_type_id: uuid.UUID | None = Field(
        None,
        title="组织类型 ID",
        description="属于指定组织类型下的角色；未提供该字段则代表角色为全局角色",
    )


@dataclass(config=BaseModelConfig)
class RolePutBody(BaseRoleBody):
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


@dataclass(config=BaseModelConfig)
class OrganizationRoleQueryBody:
    q: str | None = Field(
        None,
        title="搜索关键字",
        description="支持搜索角色名称、角色代码、角色描述",
    )
    org_type_id: uuid.UUID | None = Field(
        None,
        title="组织类型 ID",
        description="支持过滤指定组织类型下的角色",
    )
    is_deleted: bool | None = Field(
        None,
        title="角色是否禁用",
        description=(
            "支持按角色状态进行过滤，true 代表已禁用的角色，false 代表已启用的角色"
        ),
    )


@dataclass(config=BaseModelConfig)
class RoleUserBody:
    role_ids: list[uuid.UUID] = Field(
        ...,
        title="角色 ID 列表",
        description="可设置一个或多个角色",
        min_items=1,
    )
    user_ids: list[uuid.UUID] = Field(
        ...,
        title="用户 ID 列表",
        description="待添加/移除的用户 ID 列表",
        min_items=1,
    )


@dataclass(config=BaseModelConfig)
class RoleQueryBody(QueryBody):
    org_type_id: uuid.UUID | None = Field(
        None,
        title="组织类型 ID",
        description="支持过滤指定组织类型下的角色",
    )
    include_global_roles: bool = Field(
        True,
        title="是否包含全局角色",
        description="默认为 true，设为 false 代表仅查询组织类型角色",
    )
