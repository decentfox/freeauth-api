from __future__ import annotations

from enum import Enum
from typing import Any, List

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


class BaseModelConfig:
    anystr_strip_whitespace = True
    error_msg_templates = {
        "value_error.missing": "该字段为必填项",
        "type_error.none.not_allowed": "该字段不得为空",
        "type_error.uuid": "ID格式错误",
        "value_error.list.min_items": "请至少选择一项",
    }


class FilterOperatorEnum(str, Enum):
    eq = "eq"
    neq = "neq"
    gt = "gt"
    gte = "gte"
    lt = "lt"
    lte = "lte"
    ct = "ct"
    nct = "nct"

    def __int__(self):
        self.expr = ""

    def format(self, *args: object, **kwargs: object) -> str:
        return self.expr.format(*args, **kwargs)


FilterOperatorEnum.eq.expr = "{0} = {1}"
FilterOperatorEnum.neq.expr = "({0} != {1}) ?? true"
FilterOperatorEnum.gt.expr = "{0} > {1}"
FilterOperatorEnum.gte.expr = "{0} >= {1}"
FilterOperatorEnum.lt.expr = "{0} < {1}"
FilterOperatorEnum.lte.expr = "{0} <= {1}"
FilterOperatorEnum.ct.expr = "contains({0}, {1})"
FilterOperatorEnum.nct.expr = "(NOT contains({0}, {1})) ?? true"


@dataclass
class FilterItem:
    field: str = Field(..., title="字段名")
    operator: FilterOperatorEnum = Field(
        ...,
        title="运算符",
    )
    value: Any = Field(..., title="值")


@dataclass(config=BaseModelConfig)
class QueryBody:
    q: str | None = Field(
        None,
        title="搜索关键字",
        description="支持搜索用户姓名、用户名、手机号、邮箱",
        example="张三",
    )
    order_by: List[str] | None = Field(
        None,
        title="排序字段",
        description=(
            "支持多个排序字段，需降序排列时在字段前加 '-' 前缀，例如"
            " '-created_at'"
        ),
        example='["username", "-created_at"]',
    )
    filter_by: List[FilterItem] | None = Field(
        None,
        title="筛选条件",
        description=(
            "支持多个筛选条件，每个筛选条件包含 field（字段名）, operator"
            ' （运算符）, value（值）三个数据，例如： {"field": "mobile",'
            ' "operator": "eq", "value": "13800000000"}。'
            "支持的运算符有：eq（等于）, neq（不等于）, gt（大于）,"
            " gte（大于等于）, lt（小于）, lte（小于等于）, ct（包含）,"
            " nct（不包含）"
        ),
        example=(
            '[{"field": "mobile", "operator": "eq", "value": "13800000000"}]'
        ),
    )
    page: int | None = Field(
        1, title="分页页码", description="起始页码默认为 1"
    )
    per_page: int | None = Field(
        20,
        title="分页大小",
        description="默认为 20，取值为 1~100",
        ge=1,
        le=100,
    )

    @property
    def ordering_expr(self) -> str:
        return (
            " then ".join(
                f".{field[1:]} desc" if field.startswith("-") else f".{field}"
                for field in self.order_by
            )
            if self.order_by
            else ".created_at desc"
        )

    def get_filtering_expr(self, type_mapping: dict[str, str]) -> str:
        if not self.filter_by:
            return "true"

        ret: list = []
        for item in self.filter_by:
            val_type = type_mapping.get(item.field, "str")
            ret.append(
                item.operator.format(
                    f".{item.field}", f"<{val_type}>'{item.value}'"
                )
            )
        return " and ".join(ret)


class PaginatedData(BaseModel):
    total: int = Field(..., title="数据总数量")
    rows: list = Field(..., title="数据列表")
    per_page: int = Field(..., title="当前分页大小")
    page: int = Field(..., title="当前分页页码")
    last: int = Field(..., title="最后一页页码")
