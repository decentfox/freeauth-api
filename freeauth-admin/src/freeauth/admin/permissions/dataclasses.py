from __future__ import annotations

import uuid

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

from ..dataclasses import FilterItem  # noqa
from ..dataclasses import BaseModelConfig, QueryBody


@dataclass(config=BaseModelConfig)
class BasePermissionBody:
    name: str = Field(
        ...,
        title="名称",
        description="权限名称",
        min_length=1,
    )
    code: str = Field(
        ...,
        title="代码",
        description="权限代码",
        min_length=1,
    )
    description: str | None = Field(
        None,
        title="描述",
        description="权限描述",
    )
    application_id: uuid.UUID = Field(
        ...,
        title="所属应用",
        description="所属应用 ID",
    )
    tags: list[str] = Field(
        None,
        title="关联标签",
        description="关联标签 ID 或名称列表",
    )

    @validator("code", pre=True)
    def convert_to_uppercase(cls, v):
        return v.upper() if v else v


@dataclass(config=BaseModelConfig)
class PermissionStatusBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="权限 ID 列表",
        description="待变更状态的权限 ID 列表",
        min_items=1,
    )
    is_deleted: bool = Field(
        ...,
        title="是否禁用",
        description="true 为禁用权限，false 为启用权限",
    )


@dataclass(config=BaseModelConfig)
class PermissionDeleteBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="权限 ID 列表",
        description="待删除的权限 ID 列表",
    )


@dataclass(config=BaseModelConfig)
class PermissionPutBody(BasePermissionBody):
    is_deleted: bool | None = Field(
        None,
        title="是否禁用",
        description="true 为禁用权限，false 为启用权限；该字段为空时，不做任何更新",
    )


@dataclass(config=BaseModelConfig)
class PermRoleBody:
    role_ids: list[uuid.UUID] = Field(
        ...,
        title="角色 ID 列表",
        description="可设置一个或多个角色",
        min_items=1,
    )
    permission_ids: list[uuid.UUID] = Field(
        ...,
        title="权限 ID",
        description="待添加/移除的权限 ID 列表",
        min_items=1,
    )


@dataclass(config=BaseModelConfig)
class PermissionQueryBody(QueryBody):
    application_id: uuid.UUID | None = Field(
        None,
        title="所属应用 ID",
        description="支持过滤指定应用下的权限",
    )
