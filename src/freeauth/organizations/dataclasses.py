from __future__ import annotations

import uuid

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

from ..dataclasses import FilterItem  # noqa
from ..dataclasses import BaseModelConfig, QueryBody
from ..query_api import GetOrganizationNodeResult


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
        description="组织类型名称",
        min_length=1,
        max_length=20,
    )
    code: str = Field(
        ...,
        title="Code",
        description="组织类型 Code",
        min_length=1,
    )
    description: str | None = Field(
        None,
        title="描述",
        description="组织类型描述",
    )

    @validator("code", pre=True)
    def convert_code_to_uppercase(cls, v):
        return v.upper() if v else v


@dataclass(config=OrgTypeBodyConfig)
class OrgTypePutBody:
    name: str | None = Field(
        None,
        title="名称",
        description="组织类型名称，该字段为空时，不做任何更新",
        max_length=20,
    )
    code: str | None = Field(
        None,
        title="Code",
        description="组织类型 Code，该字段为空时，不做任何更新",
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

    @validator("code", pre=True)
    def convert_code_to_uppercase(cls, v):
        return v.upper() if v else v


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


class EnterpriseBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.any_str.min_length": "该字段为必填项",
        "value_error.missing": "该字段为必填项",
        "value_error.str.regex": (
            "纳税识别号格式有误，仅支持15、18 或 20 位数字与字母"
        ),
        "type_error.none.not_allowed": "该字段不得为空",
        "type_error.uuid": "企业机构ID格式错误",
    }


@dataclass(config=EnterpriseBodyConfig)
class EnterprisePutBody:
    code: str | None = Field(
        None,
        title="企业机构 Code",
        description="企业机构的唯一标识符，同一组织类型下唯一，可用于获取企业信息",
    )
    name: str = Field(
        ...,
        title="企业名称",
        description="企业名称",
        min_length=1,
    )
    tax_id: str | None = Field(
        None,
        title="纳税识别号",
        description="15、18 或 20 位纳税识别号",
        regex=r"^([A-Za-z0-9]{15}|[A-Za-z0-9]{18}|[A-Za-z0-9]{20})$",
    )
    issuing_bank: str | None = Field(
        None,
        title="开户行名称",
        description="企业开户行名称",
    )
    bank_account_number: str | None = Field(
        None,
        title="银行账号",
        description="企业银行账号",
    )
    contact_address: str | None = Field(
        None,
        title="办公地址",
        description="企业办公地址",
    )
    contact_phone_num: str | None = Field(
        None,
        title="办公电话",
        description="企业办公电话",
    )

    @validator("code", "tax_id", pre=True)
    def convert_to_uppercase(cls, v):
        return v.upper() if v else v


@dataclass(config=EnterpriseBodyConfig)
class EnterprisePostBody(EnterprisePutBody):
    org_type_id: uuid.UUID = Field(
        ..., title="组织类型 ID", description="所属组织类型"
    )


class DepartmentBodyConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.any_str.min_length": "该字段为必填项",
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
        "type_error.uuid": "上级部门ID格式错误",
    }


@dataclass(config=DepartmentBodyConfig)
class DepartmentPostOrPutBody:
    parent_id: uuid.UUID = Field(
        ..., title="所属上级部门", description="部门 ID 或企业机构 ID"
    )
    code: str | None = Field(
        None,
        title="部门 Code",
        description="部门分支的唯一标识符，同一企业机构下唯一，可用于获取部门信息",
    )
    name: str = Field(
        ...,
        title="部门名称",
        description="部门名称",
        min_length=1,
    )
    description: str | None = Field(
        None,
        title="部门描述",
        description="部门描述",
    )

    @validator("code", pre=True)
    def convert_to_uppercase(cls, v):
        return v.upper() if v else v


@dataclass(config=BaseModelConfig)
class OrganizationDeleteBody:
    ids: list[uuid.UUID] = Field(
        ...,
        title="企业机构或部门分支 ID 列表",
        description="待删除的企业机构或部门分支 ID 列表",
    )


@dataclass
class OrganizationNode(GetOrganizationNodeResult):
    children: list[OrganizationNode]


@dataclass(config=BaseModelConfig)
class OrganizationUserBody:
    organization_ids: list[uuid.UUID] = Field(
        ...,
        title="直属部门 ID 列表",
        description="可设置一个或多个部门分支或企业机构 ID",
        min_items=1,
    )
    user_ids: list[uuid.UUID] = Field(
        ...,
        title="用户 ID 列表",
        description="待添加的用户 ID 列表",
        min_items=1,
    )


@dataclass(config=BaseModelConfig)
class OrganizationUserQueryBody(QueryBody):
    include_sub_members: bool = Field(
        True,
        title="是否包含子部门下的成员",
        description="默认为 true，设为 false 代表仅查询直属成员",
    )
