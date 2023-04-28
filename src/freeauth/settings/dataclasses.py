from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic.dataclasses import dataclass

from ..dataclasses import BaseModelConfig


@dataclass(config=BaseModelConfig)
class LoginSettingBody:
    value: Any = Field(
        ...,
        title="登录配置项值",
        description="登录配置项值，支持任意 JSON 可解析的格式",
    )
