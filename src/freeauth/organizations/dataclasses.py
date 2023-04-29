from __future__ import annotations

import uuid

from pydantic import Field, validator
from pydantic.dataclasses import dataclass


class OrgTypeBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.any_str.min_length": "该字段为必填项",
        "value_error.any_str.max_length": (
            "最大支持的长度为{limit_value}个字符"
        ),
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
        "type_error.uuid": "组织类型ID格式错误",
    }


@dataclass(config=OrgTypeBodyConfig)
class OrgTypePostBody:
    name: str = Field(
        ...,
        title="名称",
        description="组织类型名称（必填项）",
        min_length=1,
        max_length=20,
    )
    description: str | None = Field(
        None,
        title="描述",
        description="组织类型描述（选填项）",
    )


@dataclass(config=OrgTypeBodyConfig)
class OrgTypePutBody:
    name: str | None = Field(
        None,
        title="名称",
        description="组织类型名称，该字段为空时，不做任何更新",
        max_length=20,
    )
    description: str | None = Field(
        None,
        title="描述",
        description="组织类型描述，该字段为空时，不做任何更新",
    )
    is_deleted: bool | None = Field(
        None,
        title="是否禁用",
        description="true 为禁用组织类型，false 为启用组织类型；该字段为空时，不做任何更新",
    )

    @validator("*", pre=True)
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


@dataclass(config=OrgTypeBodyConfig)
class OrgTypeStatusBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="组织类型 ID 列表",
        description="待变更状态的组织类型 ID 列表",
        min_items=1,
    )
    is_deleted: bool = Field(
        ...,
        title="是否禁用",
        description="true 为禁用组织类型，false 为启用组织类型",
    )


@dataclass(config=OrgTypeBodyConfig)
class OrgTypeDeleteBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="组织类型 ID 列表",
        description="待删除的组织类型 ID 列表",
    )
