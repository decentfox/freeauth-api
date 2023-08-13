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

from pydantic import Field
from pydantic.dataclasses import dataclass

from ..dataclasses import BaseModelConfig


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
    tags: list[str] = Field(
        None,
        title="关联标签",
        description="关联标签 ID 或名称列表",
    )


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
class PermissionTagDeleteBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="权限标签 ID 列表",
        description="待删除的权限标签 ID 列表",
    )


@dataclass(config=BaseModelConfig)
class PermissionTagUpdateBody:
    name: str = Field(
        ...,
        title="名称",
        description="权限标签名称",
        min_length=1,
    )


@dataclass(config=BaseModelConfig)
class PermissionTagReorderBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="权限标签 ID 列表",
        description="重新排序后的权限标签 ID 列表",
    )
