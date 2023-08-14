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
class BaseApplicationBody:
    name: str = Field(
        ...,
        title="名称",
        description="应用名称",
        min_length=1,
    )
    description: str | None = Field(
        None,
        title="描述",
        description="应用描述",
    )


@dataclass(config=BaseModelConfig)
class ApplicationStatusBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="应用 ID 列表",
        description="待变更状态的应用 ID 列表",
        min_items=1,
    )
    is_deleted: bool = Field(
        ...,
        title="是否禁用",
        description="true 为禁用应用，false 为启用应用",
    )


@dataclass(config=BaseModelConfig)
class ApplicationDeleteBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="应用 ID 列表",
        description="待删除的应用 ID 列表",
    )
