from __future__ import annotations

from pydantic import Field
from pydantic.dataclasses import dataclass

from ..base import BaseModelConfig


@dataclass(config=BaseModelConfig)
class LoginSettingBody:
    value: str = Field(
        ...,
        title="登录配置项值",
        description="登录配置项值，JSON 字符串格式",
    )
